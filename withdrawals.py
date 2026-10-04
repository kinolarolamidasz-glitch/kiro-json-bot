from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database import Database
from states import WithdrawStates
from keyboards import main_menu, payment_methods, withdrawal_actions, saved_cards, cancel_inline
from services.payment_service import format_money
from config import Config
import re

router = Router()

CARD_RE = re.compile(r'^\d{16,19}$')
PHONE_RE = re.compile(r'^(?:\+?998)?\d{9}$')

def _normalize_recipient(value: str) -> str | None:
    raw = (value or '').strip()
    compact = re.sub(r'[\s()\-]', '', raw)
    if CARD_RE.fullmatch(compact):
        return compact
    if compact.startswith('+998') and PHONE_RE.fullmatch(compact):
        return '+998' + compact[4:]
    if compact.startswith('998') and PHONE_RE.fullmatch(compact):
        return '+998' + compact[3:]
    if len(compact) == 9 and compact.isdigit() and compact[0] == '9':
        return '+998' + compact
    return None

def _mask_recipient(value: str) -> str:
    compact = re.sub(r'[\s()\-]', '', value or '')
    if CARD_RE.fullmatch(compact):
        return compact[:4] + '*' * (len(compact) - 8) + compact[-4:]
    if compact.startswith('+998') and len(compact) == 13:
        return '+998*******' + compact[-2:]
    return '****' + compact[-4:] if len(compact) >= 4 else '****'

@router.message(F.text == '💸 Pul chiqarish')
async def start(m: Message, state: FSMContext, db: Database):
    await state.clear()
    u = db.user(m.from_user.id)
    minimum = int(db.setting('min_withdrawal', '10000'))
    if not u or u['balance'] < minimum:
        return await m.answer(f'❌ Balans yetarli emas.\n💰 Balans: {format_money(u["balance"] if u else 0)}\n💸 Minimum: {format_money(minimum)}')
    await state.set_state(WithdrawStates.waiting_amount)
    await m.answer(f'💸 <b>PUL CHIQARISH</b>\n\nSummani kiriting.\n💰 Balans: {format_money(u["balance"])}\n💸 Minimum: {format_money(minimum)}\n\n/cancel — bekor qilish.', parse_mode='HTML', reply_markup=cancel_inline())

@router.message(WithdrawStates.waiting_amount, F.text)
async def amount(m: Message, state: FSMContext, db: Database):
    try: amount_value = int(m.text.replace(' ', '').replace(',', '').replace('_', ''))
    except ValueError: return await m.answer('❌ Faqat son kiriting.')
    u = db.user(m.from_user.id); minimum = int(db.setting('min_withdrawal', '10000'))
    if amount_value < minimum: return await m.answer(f'❌ Minimum: {format_money(minimum)}')
    if amount_value > u['balance']: return await m.answer('❌ Balans yetarli emas.')
    methods = db.payment_methods(True)
    if not methods: return await m.answer('❌ Faol to‘lov usuli yo‘q.')
    await state.update_data(amount=amount_value)
    await state.set_state(WithdrawStates.waiting_method)
    await m.answer('💳 <b>To‘lov usulini tanlang:</b>', parse_mode='HTML', reply_markup=payment_methods(methods, 'wdmethod'))

@router.callback_query(WithdrawStates.waiting_method, F.data.startswith('wdmethod:'))
async def method(c: CallbackQuery, state: FSMContext, db: Database):
    try: r = db.payment_method(int(c.data.split(':')[1]))
    except ValueError: return await c.answer('Noto‘g‘ri usul.', show_alert=True)
    if not r or not r['enabled']: return await c.answer('Usul faol emas.', show_alert=True)
    await state.update_data(method=r['name'])
    cards = db.cards(c.from_user.id)
    await state.set_state(WithdrawStates.waiting_card)
    if cards:
        await c.message.answer('💳 Saqlangan kartangizdan birini tanlang yoki yangi karta/recipient kiriting:', reply_markup=saved_cards(cards, 'wdcard'))
    else:
        await c.message.answer('💳 Karta raqami yoki telefon raqamini yuboring.\n\n💳 8600123456789012\n📱 +998901234567\n\nFaqat shu ikki format qabul qilinadi.', reply_markup=cancel_inline())
    await c.answer()

@router.callback_query(WithdrawStates.waiting_card, F.data.startswith('wdcard:'))
async def choose_card(c: CallbackQuery, state: FSMContext, db: Database, config: Config):
    value = c.data.split(':', 1)[1]
    if value == 'new':
        await state.set_state(WithdrawStates.waiting_recipient)
        await c.message.answer('📋 Karta raqami yoki telefon raqamini yuboring.\n\n💳 8600123456789012\n📱 +998901234567\n\nFaqat shu ikki format qabul qilinadi.', reply_markup=cancel_inline())
        await c.answer(); return
    try: cid = int(value)
    except ValueError: return await c.answer('Noto‘g‘ri karta.', show_alert=True)
    card = db.card(cid, c.from_user.id)
    if not card: return await c.answer('Karta topilmadi.', show_alert=True)
    await state.update_data(recipient=card['number'], note=f'Saqlangan karta: {card["label"]}')
    await _create(c.message, c.from_user.id, state, db, c.bot, config)
    await c.answer()

@router.message(WithdrawStates.waiting_card, F.text)
async def recipient_without_saved_button(m: Message, state: FSMContext, db: Database, config: Config):
    await _save_recipient_text(m, state, db, config)

@router.message(WithdrawStates.waiting_recipient, F.text)
async def recipient(m: Message, state: FSMContext, db: Database, config: Config):
    await _save_recipient_text(m, state, db, config)

async def _save_recipient_text(m: Message, state: FSMContext, db: Database, config: Config):
    parts = m.text.split('|', 1)
    recipient_value = parts[0].strip()
    note = parts[1].strip() if len(parts) > 1 else '-'
    normalized = _normalize_recipient(recipient_value)
    if not normalized:
        return await m.answer(
            '❌ Faqat karta raqami yoki telefon raqami qabul qilinadi.\n\n'
            '💳 Karta: 8600 1234 5678 9012\n'
            '📱 Telefon: +998 90 123 45 67'
        )
    await state.update_data(recipient=normalized, note=note[:500])
    await _create(m, m.from_user.id, state, db, m.bot, config)

async def _create(message, tg_id, state, db, bot, config):
    d = await state.get_data()
    wid = db.create_withdrawal(tg_id, int(d['amount']), d['method'], d['recipient'], d.get('note', '-'))
    if not wid:
        return await message.answer('❌ Withdrawal yaratilmadi. Balans yoki kutilayotgan withdrawalni tekshiring.')
    await state.clear()
    await message.answer(f'⏳ Withdrawal #{wid} qabul qilindi.\n💰 {format_money(d["amount"])}', reply_markup=main_menu())
    row = db.withdrawal(wid)
    text = (f'💸 <b>YANGI WITHDRAWAL #{wid}</b>\n'
            f'👤 @{row["username"] or "yo‘q"}\n'
            f'🆔 {row["telegram_user_id"]}\n'
            f'💰 {format_money(row["amount"])}\n'
            f'💳 {row["payment_method"]}\n'
            f'📋 {row["recipient"]}\n'
            f'📝 {row["note"] or "-"}')
    for aid in config.admin_ids:
        try:
            await bot.send_message(aid, text, reply_markup=withdrawal_actions(wid), parse_mode='HTML')
        except Exception:
            pass

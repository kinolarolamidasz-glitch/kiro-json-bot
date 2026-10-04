import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database import Database
from states import CardStates
from keyboards import cards_menu, card_manage, main_menu, cancel_inline

router = Router()
CARD_RE = re.compile(r'^\d{16,19}$')

def clean_card(value: str) -> str:
    return re.sub(r'[\s-]', '', value or '')

@router.message(F.text == '💳 Kartalarim')
async def cards_home(m: Message, db: Database, state: FSMContext):
    current = await state.get_state()
    if current in ('WithdrawStates:waiting_card', 'WithdrawStates:waiting_recipient'):
        return await m.answer('💸 Pul chiqarish jarayonidasiz. Bu bosqichda faqat karta raqami yoki telefon raqamini yuboring.\n/cancel — bekor qilish.')
    await state.clear()
    rows = db.cards(m.from_user.id)
    text = '💳 <b>KARTALARIM</b>\n\n'
    text += 'Saqlangan karta bo‘lsa, pul chiqarishda qayta yozishingiz shart emas.\n\n'
    text += '\n'.join(f'💳 {r["label"]} •••• {r["number"][-4:]}' for r in rows) if rows else 'Hozircha saqlangan karta yo‘q.'
    await m.answer(text, parse_mode='HTML', reply_markup=cards_menu(rows))

@router.callback_query(F.data == 'cards:home')
async def cards_home_cb(c: CallbackQuery, db: Database):
    rows = db.cards(c.from_user.id)
    text = '💳 <b>KARTALARIM</b>\n\n' + ('\n'.join(f'💳 {r["label"]} •••• {r["number"][-4:]}' for r in rows) if rows else 'Hozircha saqlangan karta yo‘q.')
    await c.message.answer(text, parse_mode='HTML', reply_markup=cards_menu(rows))
    await c.answer()

@router.callback_query(F.data == 'cardadd')
async def card_add(c: CallbackQuery, state: FSMContext):
    await state.set_state(CardStates.waiting_number)
    await c.message.answer('💳 Karta raqamini yuboring.\nMasalan: <code>8600123456789012</code>', parse_mode='HTML', reply_markup=cancel_inline())
    await c.answer()

@router.message(CardStates.waiting_number, F.text)
async def card_number(m: Message, state: FSMContext):
    number = clean_card(m.text)
    if not CARD_RE.fullmatch(number):
        return await m.answer('❌ Karta raqami noto‘g‘ri. 16–19 xonali raqam yuboring.')
    await state.update_data(card_number=number)
    await state.set_state(CardStates.waiting_name)
    await m.answer('🏷 Karta nomini yuboring. Masalan: Asosiy karta', reply_markup=cancel_inline())

@router.message(CardStates.waiting_name, F.text)
async def card_name(m: Message, state: FSMContext, db: Database):
    label = m.text.strip()[:40]
    if len(label) < 2:
        return await m.answer('❌ Karta nomi juda qisqa.')
    data = await state.get_data()
    try:
        cid = db.add_card(m.from_user.id, label, data['card_number'])
    except Exception:
        return await m.answer('❌ Bu karta allaqachon saqlangan.')
    await state.clear()
    await m.answer(f'✅ Karta saqlandi. •••• {data["card_number"][-4:]}', reply_markup=main_menu())

@router.callback_query(F.data.startswith('cardmanage:'))
async def card_manage_cb(c: CallbackQuery, db: Database):
    try: cid = int(c.data.split(':')[1])
    except ValueError: return await c.answer('Noto‘g‘ri karta.', show_alert=True)
    r = db.card(cid, c.from_user.id)
    if not r: return await c.answer('Karta topilmadi.', show_alert=True)
    await c.message.answer(f'💳 <b>{r["label"]}</b>\n•••• {r["number"][-4:]}', parse_mode='HTML', reply_markup=card_manage(r))
    await c.answer()

@router.callback_query(F.data.startswith('carddelete:'))
async def card_delete(c: CallbackQuery, db: Database):
    try: cid = int(c.data.split(':')[1])
    except ValueError: return await c.answer('Noto‘g‘ri karta.', show_alert=True)
    if not db.delete_card(cid, c.from_user.id): return await c.answer('Karta topilmadi.', show_alert=True)
    await c.answer('🗑 Karta o‘chirildi.', show_alert=True)
    rows = db.cards(c.from_user.id)
    await c.message.answer('💳 <b>KARTALARIM</b>', parse_mode='HTML', reply_markup=cards_menu(rows))

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from html import escape
from database import Database
from states import TopupStates
from keyboards import main_menu, topup_cards, cancel_inline, topup_actions
from services.payment_service import format_money
from config import Config

router=Router()

def _mask_card(n):
    n=''.join(ch for ch in (n or '') if ch.isdigit())
    return n[:4]+'*'*(max(0,len(n)-8))+n[-4:] if len(n)>=8 else '****'

@router.message(F.text == '➕ Balans to‘ldirish')
async def start(m: Message,state:FSMContext,db:Database):
    await state.clear()
    cards=db.balance_cards(True)
    if not cards:
        return await m.answer('❌ Hozircha balans to‘ldirish uchun karta mavjud emas.\nAdmin karta qo‘shgach qayta urinib ko‘ring.',reply_markup=main_menu())
    await state.set_state(TopupStates.waiting_amount)
    await m.answer('➕ <b>BALANS TO‘LDIRISH</b>\n\nTo‘ldirmoqchi bo‘lgan summani kiriting.\nMasalan: <code>50000</code>',parse_mode='HTML',reply_markup=cancel_inline())

@router.message(TopupStates.waiting_amount,F.text)
async def amount(m:Message,state:FSMContext,db:Database):
    try: amount=int(m.text.replace(' ','').replace(',','').replace('_',''))
    except ValueError:return await m.answer('❌ Faqat summa kiriting. Masalan: 50000')
    if amount<1000:return await m.answer('❌ Minimal balans to‘ldirish: 1 000 so‘m.')
    cards=db.balance_cards(True)
    if not cards:return await m.answer('❌ Faol karta mavjud emas.')
    await state.update_data(amount=amount)
    await state.set_state(TopupStates.waiting_proof)
    await state.update_data(awaiting_card=True)
    # temporarily use card selection callback; state is still waiting_proof, so callback works
    await m.answer('💳 <b>To‘lov uchun kartani tanlang:</b>',parse_mode='HTML',reply_markup=topup_cards(cards))

@router.callback_query(TopupStates.waiting_proof,F.data.startswith('topupcard:'))
async def card(c:CallbackQuery,state:FSMContext,db:Database):
    try:cid=int(c.data.split(':')[1])
    except ValueError:return await c.answer('Noto‘g‘ri karta.',show_alert=True)
    r=db.balance_card(cid)
    if not r or not r['enabled']:return await c.answer('Karta faol emas.',show_alert=True)
    d=await state.get_data()
    await state.update_data(card_id=cid,card_label=r['label'])
    await c.message.answer(
        f'💳 <b>{escape(r["label"])}</b>\n'
        f'Karta: <code>{escape(r["number"])}</code>\n'
        f'{escape(r["note"] or "")}\n\n'
        f'💰 To‘lov summasi: <b>{format_money(d["amount"])}</b>\n\n'
        'To‘lovni amalga oshirgach, tasdiqlovchi ma’lumotni yuboring.',
        parse_mode='HTML',reply_markup=cancel_inline())
    await c.answer()

@router.message(TopupStates.waiting_proof)
async def proof(m:Message,state:FSMContext,db:Database,config:Config):
    d=await state.get_data()
    if not d.get('card_id'):
        return await m.answer('❌ Avval to‘lov kartasini tanlang.')
    if m.text:
        proof_type='text'; proof=m.text[:4000]
    elif m.photo:
        proof_type='photo'; proof=m.photo[-1].file_id
    elif m.document:
        proof_type='document'; proof=m.document.file_id
    else:
        return await m.answer('❌ Tasdiqlovchi ma’lumot yuboring.')
    tid=db.create_topup(m.from_user.id,int(d['amount']),int(d['card_id']),proof_type,proof)
    if not tid:return await m.answer('❌ Balans to‘ldirish buyurtmasi yaratilmadi. Qaytadan urinib ko‘ring.')
    await state.clear()
    t=db.topup(tid)
    await m.answer(f'✅ <b>To‘lov so‘rovi qabul qilindi</b>\n🆔 #{tid}\n💰 {format_money(t["amount"])}\n⏳ Admin tasdiqlashini kuting.',parse_mode='HTML',reply_markup=main_menu())
    uname=f'@{t["username"]}' if t["username"] else 'username yo‘q'
    text=(f'💰 <b>YANGI BALANS TO‘LDIRISH #{tid}</b>\n\n'
          f'👤 Foydalanuvchi: <b>{escape(t["full_name"])}</b>\n🔗 {escape(uname)}\n'
          f'🆔 <code>{t["telegram_user_id"]}</code>\n💰 Summa: <b>{format_money(t["amount"])}</b>\n'
          f'💳 Karta: {escape(t["card_label"])} •••• {escape(t["card_number"][-4:])}\n'
          f'🕐 {escape(t["created_at"])}\n📎 Tasdiq: {escape(proof_type)}')
    for aid in config.admin_ids:
        try:
            await m.bot.send_message(aid,text,parse_mode='HTML',reply_markup=topup_actions(tid))
            if proof_type=='photo': await m.bot.send_photo(aid,proof,caption=f'🧾 Balans to‘ldirish #{tid}')
            elif proof_type=='document': await m.bot.send_document(aid,proof,caption=f'🧾 Balans to‘ldirish #{tid}')
        except Exception:pass

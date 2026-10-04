from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from html import escape
from database import Database
from config import Config
from states import JsonServiceStates
from keyboards import main_menu, cancel_inline, json_service_admin_actions
from services.payment_service import format_money

router = Router()

@router.message(F.text == '📝 JSON tayyorlash')
async def start(m: Message, state: FSMContext, db: Database):
    await state.clear()
    price = db.json_service_price()
    await state.set_state(JsonServiceStates.waiting_request)
    await m.answer(
        f'📝 <b>JSON TAYYORLASH XIZMATI</b>\n\n'
        f'💰 Narxi: <b>{format_money(price)}</b>\n\n'
        'JSON tayyorlash uchun kerakli ma’lumotlarni yuboring.\n'
        '📌 Ma’lumotlarni imkon qadar to‘liq va aniq yuboring.\n\n'
        '/cancel — bekor qilish.',
        parse_mode='HTML', reply_markup=cancel_inline())

@router.message(JsonServiceStates.waiting_request, F.text)
async def receive_request(m: Message, state: FSMContext, db: Database, config: Config):
    text=(m.text or '').strip()
    if len(text)<3:
        return await m.answer('❌ Kerakli ma’lumotlarni to‘liqroq yuboring.')
    u=db.user(m.from_user.id)
    price=db.json_service_price()
    if not u or u['balance'] < price:
        await state.clear()
        return await m.answer(
            f'❌ Balansingiz yetarli emas.\n\n'
            f'💰 Kerak: {format_money(price)}\n'
            f'💳 Balansingiz: {format_money(u["balance"] if u else 0)}\n\n'
            '➕ Avval balansni to‘ldiring.',
            reply_markup=main_menu())
    oid=db.create_json_service_order(m.from_user.id,text)
    if not oid:
        return await m.answer('❌ Buyurtma yaratilmadi. Balansingizni tekshirib qayta urinib ko‘ring.')
    await state.clear()
    order=db.json_service_order(oid)
    await m.answer(
        f'✅ <b>Buyurtma qabul qilindi</b>\n\n'
        f'🆔 Buyurtma: <b>#{oid}</b>\n'
        f'💰 Xizmat narxi: <b>{format_money(price)}</b>\n'
        f'💳 Balansdan yechildi.\n\n'
        '⏳ JSON tayyorlanmoqda.',
        parse_mode='HTML', reply_markup=main_menu())
    uname=f'@{order["username"]}' if order["username"] else 'username yo‘q'
    admin_text=(
        f'📝 <b>YANGI JSON XIZMATI #{oid}</b>\n\n'
        f'👤 Foydalanuvchi: <b>{escape(order["full_name"])}</b>\n'
        f'🔗 {escape(uname)}\n'
        f'🆔 <code>{order["telegram_user_id"]}</code>\n'
        f'💰 Narx: <b>{format_money(order["price"])}</b>\n'
        f'🕐 {escape(order["created_at"])}\n\n'
        f'📋 <b>Kerakli ma’lumotlar:</b>\n<pre>{escape(order["request_text"])}</pre>')
    for aid in config.admin_ids:
        try:
            await m.bot.send_message(aid,admin_text,parse_mode='HTML',reply_markup=json_service_admin_actions(oid))
        except Exception:
            pass

@router.callback_query(F.data.startswith('jsnoop:'))
async def noop(c: CallbackQuery):
    await c.answer()

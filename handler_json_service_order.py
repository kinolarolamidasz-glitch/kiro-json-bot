from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from html import escape
from database import Database
from config import Config
from states import JsonServiceStates
from keyboards import main_menu, cancel_inline, json_service_admin_actions, json_source_menu
from payment_service import format_money

router = Router()

@router.message(F.text == '📝 JSON tayyorlash')
async def start(m: Message, state: FSMContext, db: Database):
    await state.clear()
    price = db.json_service_price()
    await state.set_state(JsonServiceStates.waiting_source)
    await m.answer(
        f'📝 <b>JSON TAYYORLASH</b>\n\n'
        f'💰 Narxi: <b>{format_money(price)}</b>\n\n'
        'Kerakli ma’lumotlarni yuboring.\n'
        'Avval ma’lumot qaysi manbadan ekanini tanlang:',
        parse_mode='HTML', reply_markup=json_source_menu())

@router.callback_query(JsonServiceStates.waiting_source, F.data.startswith('jssource:'))
async def choose_source(c: CallbackQuery, state: FSMContext):
    source = c.data.split(':', 1)[1].strip()
    await state.update_data(source=source)
    await state.set_state(JsonServiceStates.waiting_request)
    await c.message.answer(
        f'✅ Manba: <b>{escape(source)}</b>\n\n'
        '📋 Endi JSONga aylantirilishi kerak bo‘lgan <b>ma’lumotlarni oddiy TEXT</b> qilib yuboring.\n'
        'Masalan: nomi, ID, link, parametrlar va kerakli boshqa ma’lumotlar.\n\n'
        '/cancel — bekor qilish.',
        parse_mode='HTML', reply_markup=cancel_inline())
    await c.answer()

@router.message(JsonServiceStates.waiting_source, F.text)
async def source_required(m: Message):
    await m.answer('👇 Avval manbani tanlang:', reply_markup=json_source_menu())

@router.message(JsonServiceStates.waiting_request, F.text)
async def receive_request(m: Message, state: FSMContext, db: Database, config: Config):
    text = (m.text or '').strip()
    if len(text) < 3:
        return await m.answer('❌ Kerakli ma’lumotlarni to‘liqroq yuboring.')
    u = db.user(m.from_user.id)
    price = db.json_service_price()
    if not u or u['balance'] < price:
        await state.clear()
        return await m.answer(
            f'❌ Balansingiz yetarli emas.\n\n💰 Kerak: {format_money(price)}\n'
            f'💳 Balansingiz: {format_money(u["balance"] if u else 0)}\n\n➕ Avval balansni to‘ldiring.',
            reply_markup=main_menu())
    data = await state.get_data()
    source = data.get('source', 'Ko‘rsatilmagan')
    request_text = text
    oid = db.create_json_service_order(m.from_user.id, request_text, source)
    if not oid:
        return await m.answer('❌ Buyurtma yaratilmadi. Balansingizni tekshirib qayta urinib ko‘ring.')
    await state.clear()
    order = db.json_service_order(oid)
    await m.answer(
        f'✅ <b>Buyurtma qabul qilindi</b>\n\n🆔 Buyurtma: <b>#{oid}</b>\n'
        f'🌐 Manba: <b>{escape(source)}</b>\n💰 Xizmat narxi: <b>{format_money(price)}</b>\n'
        '⏳ Admin JSONni tayyorlamoqda.', parse_mode='HTML', reply_markup=main_menu())
    uname = f'@{order["username"]}' if order["username"] else 'username yo‘q'
    admin_text = (
        f'📝 <b>YANGI JSON XIZMATI #{oid}</b>\n\n'
        f'👤 Foydalanuvchi: <b>{escape(order["full_name"])}</b>\n'
        f'🔗 {escape(uname)}\n🆔 <code>{order["telegram_user_id"]}</code>\n'
        f'🌐 <b>Manba:</b> {escape(source)}\n💰 Narx: <b>{format_money(order["price"])}</b>\n'
        f'🕐 {escape(order["created_at"])}\n\n📋 <b>Ma’lumot:</b>\n<pre>{escape(order["request_text"])}</pre>')
    for aid in config.admin_ids:
        try:
            await m.bot.send_message(aid, admin_text, parse_mode='HTML', reply_markup=json_service_admin_actions(oid))
        except Exception:
            pass

@router.callback_query(F.data == 'jsnoop:')
async def noop(c: CallbackQuery):
    await c.answer()

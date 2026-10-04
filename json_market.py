from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from database import Database
from states import SellStates
from keyboards import plans, main_menu, submission_actions, cancel_inline
from services.json_service import validate_json, html_code_block
from services.payment_service import format_money
from config import Config
from html import escape

router = Router()

GUIDE = (
    '📦 <b>JSON MARKET — NIMA SOTASIZ?</b>\n\n'
    '🧩 Tayyor JSON konfiguratsiya\n'
    '⚙️ Bot/API uchun JSON sozlamalar\n'
    '📁 Tayyor JSON fayl\n'
    '🛠 O‘zingiz yaratgan JSON ma’lumotlar\n\n'
    '<b>Qoidalar:</b>\n'
    '1️⃣ Faqat o‘zingizga tegishli kontentni yuboring.\n'
    '3️⃣ Zararli fayl yoki noqonuniy kontent yubormang.\n'
    '4️⃣ Xaridor uchun tushunarli, tartibli va foydalanishga tayyor bo‘lsin.\n\n'
    '👇 Avval sotuv tarifini tanlang.'
)

@router.message(F.text == '🛒 JSON sotish')
async def start(m: Message, state: FSMContext, db: Database):
    await state.clear()
    rows = db.plans(True)
    if not rows:
        return await m.answer('❌ Hozircha JSON tariflari mavjud emas.')
    await m.answer(GUIDE, reply_markup=plans(rows, 'jsonplan'), parse_mode='HTML')

@router.callback_query(F.data.startswith('jsonplan:'))
async def choose(c: CallbackQuery, state: FSMContext, db: Database):
    try: p = db.plan(int(c.data.split(':')[1]))
    except ValueError: return await c.answer('Noto‘g‘ri tarif.', show_alert=True)
    if not p or not p['enabled']:
        return await c.answer('Tarif mavjud emas.', show_alert=True)
    await state.update_data(plan=p['name'], price=p['price'])
    await state.set_state(SellStates.waiting_json)
    await c.message.answer(
        f'📦 <b>{escape(p["name"])}</b> — {format_money(p["price"])}\n\n'
        '📄 JSONni oddiy <b>TEXT</b> qilib yuboring yoki <b>.json hujjat</b> yuboring.\n'
        '🔍 JSON sintaksisi, dublikat kalitlar va xavfli maxsus qiymatlar tekshiriladi.\n\n'
        '/cancel — bekor qilish.', parse_mode='HTML', reply_markup=cancel_inline())
    await c.answer()

async def save_submission(message: Message, state: FSMContext, db: Database, config: Config, raw_text: str):
    try:
        formatted = validate_json(raw_text)
    except ValueError as e:
        return await message.answer(f'❌ {e}')
    d = await state.get_data()
    sid = db.create_submission(message.from_user.id, d['plan'], formatted, d['price'])
    await state.clear()
    await message.answer(f'✅ JSON qabul qilindi.\n🆔 #{sid}\n⏳ Admin tekshiruvini kuting.', reply_markup=main_menu())
    safe_user = escape(message.from_user.username or 'yo‘q')
    text = (f'📥 <b>YANGI JSON #{sid}</b>\n👤 @{safe_user}\n🆔 {message.from_user.id}\n'
            f'📦 {escape(d["plan"])}\n💰 {format_money(d["price"])}\n\n{html_code_block(formatted)}')
    for aid in config.admin_ids:
        try:
            if len(text) <= 4000:
                await message.bot.send_message(aid, text, reply_markup=submission_actions(sid), parse_mode='HTML')
            else:
                await message.bot.send_message(aid, f'📥 JSON #{sid} qabul qilindi. JSON katta, fayl orqali yuklab oling.', reply_markup=submission_actions(sid))
                await message.bot.send_document(aid, BufferedInputFile(formatted.encode('utf-8'), filename=f'json_{sid}.json'))
        except Exception:
            pass

@router.message(SellStates.waiting_json, F.document)
async def receive_document(m: Message, state: FSMContext, db: Database, config: Config):
    doc = m.document
    name = (doc.file_name or '').lower()
    if not name.endswith('.json'):
        return await m.answer('❌ Faqat .json hujjat yuboring.')
    if doc.file_size and doc.file_size > 35000:
        return await m.answer('❌ JSON fayl juda katta. Maksimum 35 KB.')
    try:
        tg_file = await m.bot.get_file(doc.file_id)
        buf = BytesIO()
        await m.bot.download_file(tg_file.file_path, destination=buf)
        raw = buf.getvalue().decode('utf-8-sig')
    except UnicodeDecodeError:
        return await m.answer('❌ JSON fayli UTF-8 formatida bo‘lishi kerak.')
    except Exception:
        return await m.answer('❌ Faylni o‘qib bo‘lmadi. Qaytadan yuboring.')
    await save_submission(m, state, db, config, raw)

@router.message(SellStates.waiting_json, F.text)
async def receive_text(m: Message, state: FSMContext, db: Database, config: Config):
    await save_submission(m, state, db, config, m.text)

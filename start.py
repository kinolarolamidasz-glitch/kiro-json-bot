from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import Database
from keyboards import main_menu
from services.membership_service import check_memberships, chat_link

router = Router()

def membership_keyboard(db: Database):
    rows = []
    for chat in db.required_chats(True):
        link = chat_link(chat)
        if link:
            rows.append([InlineKeyboardButton(text=f'📢 {chat["title"][:50]}', url=link)])
    rows.append([InlineKeyboardButton(text='🔄 Obunani tekshirish', callback_data='membership:check')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def is_member(message: Message, db: Database):
    ok, _ = await check_memberships(message.bot, db, message.from_user.id)
    return ok

@router.message(CommandStart())
async def start(message: Message, db: Database):
    u = db.ensure_user(message.from_user)
    if u['blocked']:
        return await message.answer('⛔ Sizning hisobingiz bloklangan.')
    if not await is_member(message, db):
        chats = db.required_chats(True)
        names='\n'.join(f'• {c["title"]}' for c in chats)
        return await message.answer(
            '🔐 <b>Majburiy obuna</b>\n\n'
            'Botdan foydalanish uchun quyidagi kanal/guruh(lar)ga qo‘shiling:\n'
            f'{names}\n\n'
            '1️⃣ Qo‘shiling\n2️⃣ “Obunani tekshirish”ni bosing.',
            reply_markup=membership_keyboard(db), parse_mode='HTML')
    text = (
        f'🤖 <b>Kiro savdo bot</b> ga xush kelibsiz, {message.from_user.first_name}! 👋\n\n'
        '🛒 <b>JSON Market</b> — tayyor JSON mahsulotlaringizni sotish uchun\n'
        '📝 <b>JSON tayyorlash</b> — ma’lumotlaringiz asosida JSON tayyorlatish\n'
        '💰 <b>Balans</b> — balans va tranzaksiyalarni kuzating\n'
        '➕ <b>Balans to‘ldirish</b> — admin tasdiqlagan to‘lov orqali\n'
        '💸 <b>Pul chiqarish</b> — karta yoki telefon raqamiga pul oling\n'
        '📦 <b>Sotuvlarim</b> — barcha JSON buyurtmalaringiz\n'
        '📜 <b>Tarix</b> — pul harakatlari\n'
        '💳 <b>Kartalarim</b> — kartani bir marta saqlang\n\n'
        '📌 <b>Qoidalar:</b> faqat o‘zingizga tegishli va sotishga haqqingiz bor JSON yuboring.\n\n'
        '👇 Kerakli bo‘limni tanlang:'
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode='HTML')

import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import load_config, Config
from database import Database
from keyboards import main_menu
from membership_service import check_memberships, chat_link
import handler_start as start
import handler_user as user
import handler_json_market as json_market
import handler_withdrawals as withdrawals
import handler_admin as admin
import handler_cards as cards
import handler_json_service_order as json_service_order
import handler_topups as topups

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

async def main():
    config = load_config()
    db = Database()
    bot = Bot(config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    membership_cache = {}
    user_touch_cache = {}
    MEMBERSHIP_TTL = 60.0
    USER_TOUCH_TTL = 20.0

    async def middleware(handler, event, data):
        data['db'] = db
        data['config'] = config
        if getattr(event, 'from_user', None):
            uid = event.from_user.id
            # SQLite is synchronous; do not write last_seen on every callback.
            now_mono = time.monotonic()
            if isinstance(event, Message) and now_mono - user_touch_cache.get(uid, 0) >= USER_TOUCH_TTL:
                db.ensure_user(event.from_user)
                user_touch_cache[uid] = now_mono
            u = db.user(uid)
            if u['blocked'] and event.from_user.id not in config.admin_ids:
                if isinstance(event, CallbackQuery):
                    await event.answer('⛔ Hisobingiz bloklangan.', show_alert=True)
                elif isinstance(event, Message):
                    await event.answer('⛔ Hisobingiz bloklangan.')
                return
            # Adminlar doim foydalanadi. /start esa o'zining alohida gate'iga ega.
            is_membership_check = isinstance(event, CallbackQuery) and event.data == 'membership:check'
            is_start = isinstance(event, Message) and bool(event.text) and event.text.split()[0].split('@')[0] == '/start'
            if event.from_user.id not in config.admin_ids and not is_membership_check and not is_start:
                if db.setting('membership_required', '0') == '1':
                    cached = membership_cache.get(uid)
                    if cached and now_mono - cached[0] < MEMBERSHIP_TTL:
                        ok, missing = cached[1], cached[2]
                    else:
                        ok, missing = await check_memberships(bot, db, uid)
                        membership_cache[uid] = (now_mono, ok, missing)
                    if not ok:
                        buttons=[]
                        for chat in db.required_chats(True):
                            link=chat_link(chat)
                            if link:
                                buttons.append([InlineKeyboardButton(text=f'📢 {chat["title"][:50]}', url=link)])
                        buttons.append([InlineKeyboardButton(text='🔄 Obunani tekshirish', callback_data='membership:check')])
                        kb=InlineKeyboardMarkup(inline_keyboard=buttons)
                        if isinstance(event, CallbackQuery):
                            await event.message.answer('🔐 Avval majburiy kanal/guruh(lar)ga qo‘shiling.', reply_markup=kb)
                            await event.answer()
                        elif isinstance(event, Message):
                            await event.answer('🔐 Avval majburiy kanal/guruh(lar)ga qo‘shiling.', reply_markup=kb)
                        return
        return await handler(event, data)

    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)
    dp.include_router(start.router)
    dp.include_router(user.router)
    dp.include_router(json_service_order.router)
    dp.include_router(topups.router)
    dp.include_router(json_market.router)
    dp.include_router(cards.router)
    dp.include_router(withdrawals.router)
    dp.include_router(admin.router)

    @dp.callback_query(F.data == 'membership:check')
    async def membership_check(c: CallbackQuery, db: Database, config: Config):
        if c.from_user.id in config.admin_ids:
            return await c.answer('Admin uchun cheklov yo‘q.')
        if db.setting('membership_required','0') != '1' or not db.required_chats(True):
            await c.message.answer('✅ Majburiy obuna o‘chiq. Botdan foydalanishingiz mumkin.', reply_markup=main_menu())
            return await c.answer('✅ Tasdiqlandi')
        ok, missing = await check_memberships(c.bot, db, c.from_user.id)
        membership_cache.pop(c.from_user.id, None)
        if ok:
            await c.message.answer('✅ Obuna tasdiqlandi. Endi botdan foydalanishingiz mumkin.', reply_markup=main_menu())
            return await c.answer('✅ Tasdiqlandi')
        await c.answer('❌ Hali barcha kanal/guruhlarga obuna bo‘lmagansiz.', show_alert=True)

    @dp.message(Command('cancel'))
    async def cancel(m: Message, state):
        await state.clear()
        await m.answer('❌ Amal bekor qilindi.', reply_markup=main_menu())

    @dp.callback_query(F.data == 'fsm:cancel')
    async def cancel_callback(c: CallbackQuery, state):
        await state.clear()
        await c.message.answer('❌ Amal bekor qilindi.', reply_markup=main_menu())
        await c.answer('Bekor qilindi')

    await bot.set_my_commands([
        BotCommand(command='start', description='Botni boshlash'),
        BotCommand(command='cancel', description='Joriy amalni bekor qilish'),
        BotCommand(command='admin', description='Admin panel')
    ])
    logger.info('Kiro savdo bot ishga tushmoqda...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot to‘xtatildi.')
    except Exception:
        logger.exception('Fatal error')
        raise

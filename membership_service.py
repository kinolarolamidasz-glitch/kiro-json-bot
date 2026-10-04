from aiogram import Bot
from database import Database

async def check_memberships(bot: Bot, db: Database, user_id: int) -> tuple[bool, list[str]]:
    """Return (ok, missing_titles). Empty required list means no restriction."""
    chats = db.required_chats(True)
    if not chats:
        return True, []
    missing = []
    for chat in chats:
        try:
            member = await bot.get_chat_member(chat['chat_id'], user_id)
            if member.status in ('left', 'kicked'):
                missing.append(chat['title'])
        except Exception:
            # Fail closed: a configured chat that cannot be checked must not bypass the gate.
            missing.append(chat['title'])
    return not missing, missing

def chat_link(chat) -> str:
    link=(chat['link'] or '').strip()
    if link:
        return link
    cid=str(chat['chat_id'])
    if cid.startswith('@'):
        return 'https://t.me/'+cid[1:]
    return ''

from aiogram import Router,F
from aiogram.types import Message
from html import escape
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import main_menu
from services.payment_service import format_money
router=Router()
@router.message(F.text=='💰 Balansim')
async def balance(m:Message,db:Database,state:FSMContext):
 await state.clear();u=db.ensure_user(m.from_user); rows=db.transactions(m.from_user.id);s=db.stats();
 with db.conn() as c:
  r=c.execute('SELECT * FROM users WHERE telegram_user_id=?',(m.from_user.id,)).fetchone(); bal=r['balance'];earned=c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='json_sale'",(r['id'],)).fetchone()[0];wd=c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status IN ('pending','processing')",(r['id'],)).fetchone()[0]
 await m.answer(f'💰 <b>BALANSIM</b>\n\n💵 Balans: <b>{format_money(bal)}</b>\n📈 Jami JSON daromad: {format_money(earned)}\n⏳ Kutilayotgan withdrawal: {format_money(wd)}',parse_mode='HTML')
@router.message(F.text=='📦 Sotuvlarim')
async def sales(m:Message,db:Database,state:FSMContext):
 await state.clear();rows=db.submissions(m.from_user.id)
 await m.answer('📦 <b>SOTUVLARIM</b>\n\n'+('\n'.join(f"#{r['id']} • {r['plan']} • {format_money(r['price'])} • {r['status']}" for r in rows) if rows else 'Hozircha sotuv yo‘q.'),parse_mode='HTML')
@router.message(F.text=='📜 Tarix')
async def history(m:Message,db:Database,state:FSMContext):
 await state.clear();rows=db.transactions(m.from_user.id)
 await m.answer('📜 <b>TRANZAKSIYALAR</b>\n\n'+('\n'.join(f"{r['created_at']} • {r['type']} • {format_money(r['amount'])} • {r['note'] or ''}" for r in rows) if rows else 'Tarix bo‘sh.'),parse_mode='HTML')
@router.message(F.text=='👤 Kabinet')
async def cabinet(m:Message,db:Database,state:FSMContext):
 await state.clear();u=db.ensure_user(m.from_user);await m.answer(f"👤 <b>KABINET</b>\n\n🆔 {u['telegram_user_id']}\n📛 {u['full_name']}\n🔗 @{u['username'] or 'yo‘q'}\n💰 Balans: {format_money(u['balance'])}\n📅 Ro‘yxatdan o‘tgan: {u['created_at']}",parse_mode='HTML')
@router.message(F.text=='❓ Yordam')
async def help_(m:Message,db:Database,state:FSMContext):
 await state.clear();await m.answer(db.setting('help_text','Yordam uchun admin bilan bog‘laning.'))

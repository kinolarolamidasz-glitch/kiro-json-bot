from aiogram import Router,F
from aiogram.filters import Command
from aiogram.types import Message,CallbackQuery,BufferedInputFile
from html import escape
from aiogram.fsm.context import FSMContext
from database import Database
from config import Config
from keyboards import *
from states import AdminStates
from services.payment_service import format_money
from services.json_service import html_code_block
from services.backup_service import make_backup
router=Router()

from datetime import datetime
import asyncio
from services.membership_service import chat_link

def _fmt_time(value):
    if not value:
        return '-'
    try:
        dt=datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return str(value)

def _admin_label(user):
    username = f'@{user.username}' if user.username else 'username yo‘q'
    return f'{username} (ID: {user.id})'

def _mask_recipient(value):
    import re
    compact=re.sub(r'[\s()\-]','',value or '')
    if compact.isdigit() and 16 <= len(compact) <= 19:
        return compact[:4] + '*'*(len(compact)-8) + compact[-4:]
    if compact.startswith('+998') and len(compact)==13:
        return '+998*******' + compact[-2:]
    return '****' + compact[-4:] if len(compact)>=4 else '****'
def _mask_name(value):
    raw=' '.join((value or '').split())
    if not raw:
        return '***'
    chars=[ch for ch in raw if ch.isalnum()]
    keep=min(3,len(chars))
    return ''.join(chars[:keep]) + '*'*max(4,len(chars)-keep)

def adm(uid,c):return uid in c.admin_ids
async def deny(c): await c.answer('⛔ Ruxsat yo‘q.',show_alert=True)
@router.message(Command('admin'))
async def admin(m:Message,config:Config):
 if not adm(m.from_user.id,config):return await m.answer('⛔ Ruxsat yo‘q.')
 await m.answer('👑 <b>ADMIN PANEL</b>\n\nBarcha boshqaruv shu yerdan.',reply_markup=admin_menu(),parse_mode='HTML')
@router.callback_query(F.data=='adm:home')
async def home(c:CallbackQuery,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await c.message.answer('👑 <b>ADMIN PANEL</b>',reply_markup=admin_menu(),parse_mode='HTML');await c.answer()
@router.callback_query(F.data=='adm:stats')
async def stats(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 s=db.stats();await c.message.answer(f'📊 <b>DASHBOARD</b>\n\n👥 Users: {s["users"]}\n🛒 JSON: {s["json"]} | ⏳ {s["json_pending"]} | ✅ {s["json_approved"]}\n💸 Withdrawal: {s["withdrawals"]} | ⏳ {s["wd_pending"]} | 🔄 {s["wd_processing"]} | ✅ {s["wd_paid"]}\n\n💰 JSON daromadi: {format_money(s["json_amount"])}',parse_mode='HTML',reply_markup=back_admin());await c.answer()
@router.callback_query(F.data=='adm:json')
async def jsons(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.pending_submissions()
 if not rows:
  with db.conn() as con:
   rows=con.execute("SELECT s.*,u.telegram_user_id,u.username,u.full_name FROM json_submissions s JOIN users u ON u.id=s.user_id WHERE s.status='processing' ORDER BY s.id DESC").fetchall()
 if not rows:await c.message.answer('📥 Pending/Processing JSON yo‘q.',reply_markup=back_admin())
 for s in rows:
  text=f'📥 <b>JSON #{s["id"]}</b>\n👤 @{escape(s["username"] or "yo‘q")}\n🆔 {s["telegram_user_id"]}\n📦 {escape(s["plan"])}\n💰 {format_money(s["price"])}\n\n{html_code_block(s["json_text"])}'
  if len(text)>4000:text=f'📥 JSON #{s["id"]}\nJSON katta. 📥 JSON tugmasidan yuklab oling.'
  await c.message.answer(text,reply_markup=submission_actions(s['id']),parse_mode='HTML')
 await c.answer()
@router.callback_query(F.data.startswith('jsonproc:'))
async def jsonproc(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 sid=int(c.data.split(':')[1]);s=db.submission(sid)
 if not s or s['status']!='pending':return await c.answer('Allaqachon ko‘rib chiqilgan.',show_alert=True)
 with db.conn() as con: con.execute("UPDATE json_submissions SET status='processing' WHERE id=? AND status='pending'",(sid,))
 await c.message.answer(f'🔄 JSON #{sid} PROCESSING. Endi tasdiqlash yoki rad etish mumkin.');await c.answer()
@router.callback_query(F.data.startswith('approve:'))
async def approve(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 sid=int(c.data.split(':')[1]);s=db.review_submission(sid,'approved')
 if not s:return await c.answer('Bu JSON tasdiqlanmaydi.',show_alert=True)
 await c.message.edit_reply_markup(reply_markup=None);await c.message.answer(f'✅ JSON #{sid} tasdiqlandi.');
 try:await c.bot.send_message(s['telegram_user_id'],f'✅ JSON #{sid} tasdiqlandi.\n💰 +{format_money(s["price"])} balansga qo‘shildi.')
 except Exception:pass
 await c.answer()
@router.callback_query(F.data.startswith('reject:'))
async def reject(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(reject_json=int(c.data.split(':')[1]));await state.set_state(AdminStates.reject_json);await c.message.answer('❌ Rad etish sababini yuboring.');await c.answer()
@router.message(AdminStates.reject_json,F.text)
async def reject_reason(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config): return
 d=await state.get_data()
 s=db.review_submission(int(d["reject_json"]),'rejected',m.text[:500]); await state.clear()
 if not s:return await m.answer("❌ JSON topilmadi yoki allaqachon ko‘rilgan.")
 await m.answer("❌ JSON rad etildi.")
 try: await m.bot.send_message(s["telegram_user_id"],f"❌ JSON #{s['id']} rad etildi.\nSabab: {s['reject_reason']}")
 except Exception: pass
@router.callback_query(F.data.startswith('download:'))
async def download(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 s=db.submission(int(c.data.split(':')[1]));
 if not s:return await c.answer('Topilmadi.',show_alert=True)
 await c.message.answer_document(BufferedInputFile(s['json_text'].encode(),filename=f'json_{s["id"]}.json'));await c.answer()
@router.callback_query(F.data.startswith('delete:'))
async def delete(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 with db.conn() as con:con.execute('DELETE FROM json_submissions WHERE id=?',(int(c.data.split(':')[1]),))
 await c.message.edit_reply_markup(reply_markup=None);await c.answer('O‘chirildi.')
@router.callback_query(F.data=='adm:withdraw')
async def withdrawals(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.withdrawals_by_status()
 for w in rows[:30]:
  await c.message.answer(f'💸 <b>#{w["id"]}</b> {w["status"]}\n👤 @{w["username"] or "yo‘q"}\n🆔 {w["telegram_user_id"]}\n💰 {format_money(w["amount"])}\n💳 {w["payment_method"]}\n📋 {w["recipient"]}\n📝 {w["note"] or "-"}',reply_markup=withdrawal_actions(w['id']),parse_mode='HTML')
 if not rows:await c.message.answer('💸 Withdrawal yo‘q.',reply_markup=back_admin())
 await c.answer()
@router.callback_query(F.data.startswith('wdproc:'))
async def wdproc(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 ok=db.set_withdrawal_processing(int(c.data.split(':')[1]));await c.answer('🔄 Processing' if ok else 'Status o‘zgarmadi.',show_alert=True)
@router.callback_query(F.data.startswith('paid:'))
async def paid(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 wid=int(c.data.split(':')[1]);w=db.finish_withdrawal(wid,True,paid_by_id=c.from_user.id,paid_by_username=c.from_user.username or '')
 if not w:return await c.answer('To‘lovni yakunlab bo‘lmadi.',show_alert=True)
 await c.message.edit_reply_markup(reply_markup=None);await c.message.answer(f'💸 #{wid} to‘landi. {w["payment_id"]}')
 try:await c.bot.send_message(w['telegram_user_id'],f'✅ Withdrawal #{wid} to‘landi.\n🆔 {w["payment_id"]}')
 except Exception:pass
 channel=db.setting('payment_channel_id','')
 if channel:
  try:
   card=_mask_recipient(w['recipient'])
   await c.bot.send_message(channel,
    f'💸 <b>TO‘LOV TASDIQLANDI</b>\n\n'
    f'🆔 Withdrawal: #{wid}\n'
    f'👤 Foydalanuvchi: <b>{escape(_mask_name(w["full_name"]))}</b>\n'
    f'💰 Summa: <b>{format_money(w["amount"])}</b>\n'
    f'💳 Usul: {escape(w["payment_method"])}\n'
    f'💳 Karta/telefon: <code>{escape(card)}</code>\n'
    f'🕐 Chiqarilgan vaqt: {_fmt_time(w["requested_at"])}\n'
    f'✅ To‘langan vaqt: {_fmt_time(w["paid_at"])}\n'
    f'🆔 To‘lov ID: <code>{escape(w["payment_id"] or "-")}</code>\n'
    f'👨‍💼 Tasdiqlagan: {escape(_admin_label(c.from_user))}',
    parse_mode='HTML')
  except Exception: pass
 await c.answer()
@router.callback_query(F.data.startswith('wreject:'))
async def wrej(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(reject_withdrawal=int(c.data.split(':')[1]));await state.set_state(AdminStates.reject_withdrawal);await c.message.answer('❌ Withdrawal rad etish sababini yuboring.');await c.answer()
@router.message(AdminStates.reject_withdrawal,F.text)
async def wrej_reason(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();w=db.finish_withdrawal(int(d['reject_withdrawal']),False,m.text[:500]);await state.clear()
 if not w:return await m.answer('❌ Withdrawal topilmadi.')
 await m.answer('❌ Withdrawal rad etildi. Balans yechilmadi.')
 try:await m.bot.send_message(w['telegram_user_id'],f'❌ Withdrawal #{w["id"]} rad etildi.\nSabab: {w["reject_reason"]}')
 except Exception:pass
@router.callback_query(F.data=='adm:plans')
async def plans_admin(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await c.message.answer('💎 <b>TARIFLAR</b>',reply_markup=plan_admin(db.plans()),parse_mode='HTML');await c.answer()
@router.callback_query(F.data.startswith('planadm:'))
async def planadm(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.plan(int(c.data.split(':')[1]));await c.message.answer(f'💎 <b>{r["name"]}</b>\n💰 {format_money(r["price"])}\nStatus: {"ON" if r["enabled"] else "OFF"}',reply_markup=plan_manage(r),parse_mode='HTML');await c.answer()
@router.callback_query(F.data=='planadd')
async def planadd(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.add_plan_name);await c.message.answer('➕ Tarif nomini yuboring.');await c.answer()
@router.message(AdminStates.add_plan_name,F.text)
async def plan_name(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 await state.update_data(plan_name=m.text.strip()[:50]);await state.set_state(AdminStates.add_plan_price);await m.answer('💰 Narxni yuboring (faqat son).')
@router.message(AdminStates.add_plan_price,F.text)
async def plan_price(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 try:p=int(m.text.replace(' ',''))
 except:return await m.answer('❌ Son kiriting.')
 if p<=0:return await m.answer('❌ Narx 0 dan katta bo‘lsin.')
 d=await state.get_data()
 try:db.add_plan(d['plan_name'],p)
 except Exception:return await m.answer('❌ Bu tarif nomi allaqachon mavjud.')
 await state.clear();await m.answer('✅ Tarif qo‘shildi.',reply_markup=admin_menu())
@router.callback_query(F.data.startswith('planprice:'))
async def planprice(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(edit_plan=int(c.data.split(':')[1]));await state.set_state(AdminStates.edit_plan_price);await c.message.answer('💰 Yangi narxni yuboring.');await c.answer()
@router.message(AdminStates.edit_plan_price,F.text)
async def plan_price_edit(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 try:p=int(m.text.replace(' ',''))
 except:return await m.answer('❌ Son kiriting.')
 d=await state.get_data();db.update_plan(d['edit_plan'],price=p);await state.clear();await m.answer('✅ Narx yangilandi.',reply_markup=admin_menu())
@router.callback_query(F.data.startswith('plantoggle:'))
async def plantoggle(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.plan(int(c.data.split(':')[1]));db.update_plan(r['id'],enabled=not r['enabled']);await c.answer('Yangilandi.');await c.message.answer('💎 Tariflar',reply_markup=plan_admin(db.plans()))
@router.callback_query(F.data.startswith('plandelete:'))
async def plandelete(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 db.delete_plan(int(c.data.split(':')[1]));await c.answer('O‘chirildi.');await c.message.answer('💎 Tariflar',reply_markup=plan_admin(db.plans()))
@router.callback_query(F.data=='adm:payments')
async def payments(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await c.message.answer('💳 <b>TO‘LOV USULLARI</b>',reply_markup=pay_admin(db.payment_methods(False)),parse_mode='HTML');await c.answer()
@router.callback_query(F.data.startswith('payadm:'))
async def payadm(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.payment_method(int(c.data.split(':')[1]));await c.message.answer(f'💳 <b>{r["name"]}</b>\n📌 {r["details"] or "Rekvizit yo‘q"}\n📝 {r["note"] or "Izoh yo‘q"}',reply_markup=pay_manage(r),parse_mode='HTML');await c.answer()
@router.callback_query(F.data=='payadd')
async def payadd(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.add_payment_name);await c.message.answer('➕ To‘lov usuli nomini yuboring. Masalan: Click');await c.answer()
@router.message(AdminStates.add_payment_name,F.text)
async def pay_name(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 await state.update_data(pay_name=m.text.strip()[:50]);await state.set_state(AdminStates.add_payment_details);await m.answer('📌 Rekvizitni yuboring.')
@router.message(AdminStates.add_payment_details,F.text)
async def pay_details(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 await state.update_data(pay_details=m.text[:1000]);await state.set_state(AdminStates.add_payment_note);await m.answer('📝 Izohni yuboring yoki - yozing.')
@router.message(AdminStates.add_payment_note,F.text)
async def pay_note(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data()
 try:db.add_payment(d['pay_name'],d['pay_details'],'' if m.text.strip()=='-' else m.text[:1000])
 except Exception:return await m.answer('❌ Bu nom allaqachon mavjud.')
 await state.clear();await m.answer('✅ To‘lov usuli qo‘shildi.',reply_markup=admin_menu())
@router.callback_query(F.data.startswith('paydetails:'))
async def paydetails(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(edit_pay=int(c.data.split(':')[1]));await state.set_state(AdminStates.edit_payment_details);await c.message.answer('📌 Yangi rekvizitni yuboring.');await c.answer()
@router.message(AdminStates.edit_payment_details,F.text)
async def edit_pd(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();db.update_payment(d['edit_pay'],details=m.text[:1000]);await state.clear();await m.answer('✅ Rekvizit yangilandi.',reply_markup=admin_menu())
@router.callback_query(F.data.startswith('paynote:'))
async def paynote(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(edit_pay=int(c.data.split(':')[1]));await state.set_state(AdminStates.edit_payment_note);await c.message.answer('📝 Yangi izohni yuboring.');await c.answer()
@router.message(AdminStates.edit_payment_note,F.text)
async def edit_pn(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();db.update_payment(d['edit_pay'],note=m.text[:1000]);await state.clear();await m.answer('✅ Izoh yangilandi.',reply_markup=admin_menu())
@router.callback_query(F.data.startswith('paytoggle:'))
async def paytoggle(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.payment_method(int(c.data.split(':')[1]));db.update_payment(r['id'],enabled=not r['enabled']);await c.answer('Yangilandi.');await c.message.answer('💳 To‘lovlar',reply_markup=pay_admin(db.payment_methods(False)))
@router.callback_query(F.data.startswith('paydelete:'))
async def paydelete(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 db.delete_payment(int(c.data.split(':')[1]));await c.answer('O‘chirildi.');await c.message.answer('💳 To‘lovlar',reply_markup=pay_admin(db.payment_methods(False)))
@router.callback_query(F.data=='adm:users')
async def users(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.all_users();await c.message.answer('👥 <b>USERS</b>\n\n'+('\n'.join(f'🆔 {r["telegram_user_id"]} | @{r["username"] or "yo‘q"} | 💰 {format_money(r["balance"])} | {"🔴" if r["blocked"] else "🟢"}' for r in rows) if rows else 'User yo‘q.'),parse_mode='HTML',reply_markup=back_admin());await c.answer()
@router.callback_query(F.data=='adm:balances')
async def balances(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.all_users();await c.message.answer('\n'.join(f'🆔 {r["telegram_user_id"]} | 💰 {format_money(r["balance"])}' for r in rows) or 'Bo‘sh.',reply_markup=back_admin());await c.answer()
@router.callback_query(F.data=='adm:transactions')
async def transactions(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 with db.conn() as con:rows=con.execute('SELECT t.*,u.telegram_user_id FROM transactions t JOIN users u ON u.id=t.user_id ORDER BY t.id DESC LIMIT 50').fetchall()
 await c.message.answer('📜 <b>TRANZAKSIYALAR</b>\n\n'+('\n'.join(f'#{r["id"]} | {r["telegram_user_id"]} | {r["type"]} | {format_money(r["amount"])} | {r["note"] or ""}' for r in rows) if rows else 'Bo‘sh.'),parse_mode='HTML',reply_markup=back_admin());await c.answer()
@router.callback_query(F.data=='adm:membership')
async def membership_admin(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.required_chats(False)
 status='🟢 ON' if db.setting('membership_required','0')=='1' else '🔴 OFF'
 text='🔐 <b>MAJBURIY OBUNA</b>\n\nStatus: '+status+'\n'
 text+='Quyidagi kanal/guruhlar talab qilinadi:\n\n'
 if rows:
  for r in rows:
   text+=f'{"🟢" if r["enabled"] else "🔴"} {escape(r["title"])}\n🆔 <code>{escape(str(r["chat_id"]))}</code>\n🔗 {escape(r["link"] or "-")}\n\n'
 else:
  text+='Hali kanal/guruh qo‘shilmagan.\n'
 await c.message.answer(text,reply_markup=required_chat_admin(rows),parse_mode='HTML');await c.answer()

@router.callback_query(F.data=='mchatadd')
async def mchatadd(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.add_required_chat_id)
 await c.message.answer(
  '➕ <b>KANAL/GURUH QO‘SHISH</b>\n\n'
  'Kanal username yoki ID yuboring.\n'
  'Masalan: <code>@mychannel</code> yoki <code>-1001234567890</code>\n\n'
  '⚠️ Bot shu kanal/guruhda <b>admin</b> bo‘lishi kerak.',
  parse_mode='HTML')
 await c.answer()

@router.message(AdminStates.add_required_chat_id,F.text)
async def mchat_id(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 raw=m.text.strip()
 if not raw:return await m.answer('❌ ID yoki @username yuboring.')
 try:
  chat=await m.bot.get_chat(raw)
  me=await m.bot.get_chat_member(chat.id,m.bot.id)
  if me.status not in ('administrator','creator'):
   return await m.answer('❌ Avval botni shu kanal/guruhga administrator qilib qo‘ying.')
 except Exception as e:
  return await m.answer('❌ Kanal/guruh topilmadi yoki botda tekshirish huquqi yo‘q. ID/@username ni tekshiring.')
 await state.update_data(required_chat_id=str(chat.id),required_chat_title=chat.title or chat.full_name or str(chat.id),required_chat_username=getattr(chat,'username',None) or '')
 await state.set_state(AdminStates.add_required_chat_link)
 derived=('https://t.me/'+chat.username) if getattr(chat,'username',None) else ''
 await m.answer(
  f'✅ Topildi: <b>{escape(chat.title or chat.full_name or str(chat.id))}</b>\n\n'
  '🔗 Endi foydalanuvchilar kirishi uchun havolani yuboring.\n'
  f'Public kanal bo‘lsa <code>-</code> yuborsangiz avtomatik olinadi: {escape(derived or "private guruh uchun invite link kerak")}',
  parse_mode='HTML')

@router.message(AdminStates.add_required_chat_link,F.text)
async def mchat_link(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data()
 link=m.text.strip()
 if link=='-':
  link=('https://t.me/'+d['required_chat_username']) if d.get('required_chat_username') else ''
 if not link and not d.get('required_chat_username'):
  return await m.answer('❌ Private kanal/guruh uchun invite link kerak.')
 if link and not (link.startswith('https://t.me/') or link.startswith('http://t.me/') or link.startswith('https://telegram.me/')):
  return await m.answer('❌ Telegram havolasini yuboring: https://t.me/...')
 try:
  db.add_required_chat(d['required_chat_id'],d['required_chat_title'],link)
 except Exception:
  return await m.answer('❌ Bu kanal/guruh allaqachon qo‘shilgan.')
 await state.clear()
 await m.answer('✅ Kanal/guruh majburiy obunaga qo‘shildi.',reply_markup=admin_menu())

@router.callback_query(F.data.startswith('mchat:'))
async def mchat_manage(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 try:r=db.required_chat(int(c.data.split(':')[1]))
 except: r=None
 if not r:return await c.answer('Topilmadi.',show_alert=True)
 await c.message.answer(
  f'🔐 <b>{escape(r["title"])}</b>\n🆔 <code>{escape(str(r["chat_id"]))}</code>\n🔗 {escape(r["link"] or "-")}\n'
  f'Status: {"🟢 ON" if r["enabled"] else "🔴 OFF"}',
  reply_markup=required_chat_manage(r),parse_mode='HTML')
 await c.answer()

@router.callback_query(F.data.startswith('mchattoggle:'))
async def mchattoggle(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 try:r=db.required_chat(int(c.data.split(':')[1]))
 except: r=None
 if not r:return await c.answer('Topilmadi.',show_alert=True)
 db.update_required_chat(r['id'],enabled=not r['enabled'])
 await c.answer('Yangilandi.')
 await c.message.answer('🔐 Majburiy obuna',reply_markup=required_chat_admin(db.required_chats(False)))

@router.callback_query(F.data.startswith('mchatdelete:'))
async def mchatdelete(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 try:cid=int(c.data.split(':')[1])
 except:return await c.answer('Noto‘g‘ri.',show_alert=True)
 db.delete_required_chat(cid)
 await c.answer('O‘chirildi.')
 await c.message.answer('🔐 Majburiy obuna',reply_markup=required_chat_admin(db.required_chats(False)))

@router.callback_query(F.data=='adm:broadcast')
async def broadcast_start(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.broadcast)
 await c.message.answer(
  '📣 <b>HAMMAGA XABAR</b>\n\n'
  'Yubormoqchi bo‘lgan xabarni shu yerga yuboring.\n'
  'Matn, rasm, video yoki hujjat yuborishingiz mumkin.\n\n'
  '/cancel — bekor qilish.',
  parse_mode='HTML')
 await c.answer()

@router.message(AdminStates.broadcast)
async def broadcast_send(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 ids=db.all_user_ids()
 await state.clear()
 sent=0;failed=0
 await m.answer(f'📣 Yuborish boshlandi...\n👥 Jami: {len(ids)}')
 for uid in ids:
  if uid==m.from_user.id:
   continue
  try:
   await m.bot.copy_message(chat_id=uid,from_chat_id=m.chat.id,message_id=m.message_id)
   sent+=1
   await asyncio.sleep(0.04)
  except Exception as e:
   failed+=1
   retry=getattr(e,'retry_after',None)
   if retry:
    try:
     await asyncio.sleep(float(retry)+0.5)
     await m.bot.copy_message(chat_id=uid,from_chat_id=m.chat.id,message_id=m.message_id)
     sent+=1; failed-=1
    except Exception: pass
 await m.answer(f'✅ <b>Tarqatish tugadi</b>\n\n📨 Yuborildi: {sent}\n❌ Yuborilmadi: {failed}',parse_mode='HTML',reply_markup=admin_menu())

@router.callback_query(F.data=='adm:channels')
async def channels(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await c.message.answer(f'📢 <b>KANALLAR</b>\n\nOfficial ID: {db.setting("official_channel_id")}\nOfficial link: {db.setting("official_channel_link")}\nPayment channel: {db.setting("payment_channel_id")}\nMajburiy obuna: {db.setting("membership_required","0")}',parse_mode='HTML',reply_markup=back_admin());await c.answer()
@router.callback_query(F.data=='adm:settings')
async def settings(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await c.message.answer(f'⚙️ <b>SOZLAMALAR</b>\n\nMinimum withdrawal: {format_money(int(db.setting("min_withdrawal","10000")))}\nMajburiy obuna: {"ON" if db.setting("membership_required","0")=="1" else "OFF"}',parse_mode='HTML',reply_markup=settings_menu());await c.answer()
@router.callback_query(F.data=='adm:backup')
async def backup(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 path=make_backup(db.path)
 with open(path,'rb') as f:data=f.read()
 await c.message.answer_document(BufferedInputFile(data,filename=path.split('/')[-1]));await c.answer()

@router.callback_query(F.data.startswith('set:'))
async def set_menu(c:CallbackQuery,state:FSMContext,db:Database,config:Config):
 if not adm(c.from_user.id,config): return await deny(c)
 key=c.data.split(':',1)[1]
 labels={'minwd':'min_withdrawal','help':'help_text','official_id':'official_channel_id','official_link':'official_channel_link','payment_channel':'payment_channel_id'}
 if key=='membership':
  if db.setting('membership_required','0')=='0' and not db.required_chats(True):
   return await c.answer('Avval Majburiy obuna bo‘limidan kamida bitta faol kanal/guruh qo‘shing.',show_alert=True)
  new='0' if db.setting('membership_required','0')=='1' else '1'
  db.set_setting('membership_required',new)
  await c.answer('Majburiy obuna: '+('ON' if new=='1' else 'OFF'),show_alert=True)
  return
 db.set_setting('admin_pending_setting',labels.get(key,key));await state.set_state(AdminStates.set_value);await c.message.answer('✏️ Yangi qiymatni yuboring.');await c.answer()

@router.message(AdminStates.set_value,F.text)
async def set_value(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config): return
 key=db.setting('admin_pending_setting')
 if key=='min_withdrawal':
  try:v=int(m.text.replace(' ',''))
  except:return await m.answer('❌ Faqat son.')
  if v<0:return await m.answer('❌ 0 dan kichik bo‘lmasin.')
 else:v=m.text[:2000]
 db.set_setting(key,v);await state.clear();await m.answer('✅ Sozlama saqlandi.',reply_markup=admin_menu())


# ========================= JSON SERVICE =========================
@router.callback_query(F.data=='adm:jsonservice')
async def jsonservice_admin(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 price=db.json_service_price()
 rows=db.pending_json_service_orders()
 text=f'📝 <b>JSON TAYYORLASH XIZMATI</b>\n\n💰 Narx: <b>{format_money(price)}</b>\n📥 Kutilayotgan buyurtmalar: <b>{len(rows)}</b>'
 await c.message.answer(text,parse_mode='HTML',reply_markup=json_service_price_admin(price))
 for o in rows:
  uname=f'@{o["username"]}' if o['username'] else 'username yo‘q'
  body=(f'📝 <b>#{o["id"]}</b>\n👤 {escape(o["full_name"])}\n🔗 {escape(uname)}\n'
        f'🆔 <code>{o["telegram_user_id"]}</code>\n💰 {format_money(o["price"])}\n'
        f'🕐 {escape(o["created_at"])}\n\n📋 <b>Ma’lumot:</b>\n<pre>{escape(o["request_text"])}</pre>')
  await c.message.answer(body,parse_mode='HTML',reply_markup=json_service_admin_actions(o['id']))
 await c.answer()

@router.callback_query(F.data=='jsprice')
async def jsprice(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.json_service_price)
 await c.message.answer('💰 JSON tayyorlash xizmatining yangi narxini yuboring.\nMasalan: 20000')
 await c.answer()

@router.message(AdminStates.json_service_price,F.text)
async def jsprice_save(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 try:p=int(m.text.replace(' ','').replace(',','').replace('_',''))
 except ValueError:return await m.answer('❌ Faqat son kiriting.')
 if p<=0:return await m.answer('❌ Narx 0 dan katta bo‘lishi kerak.')
 db.set_setting('json_service_price',p)
 await state.clear();await m.answer(f'✅ JSON xizmat narxi {format_money(p)} qilib saqlandi.',reply_markup=admin_menu())

@router.callback_query(F.data.startswith('jsdeliver:'))
async def jsdeliver(c:CallbackQuery,state:FSMContext,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 try:oid=int(c.data.split(':')[1])
 except ValueError:return await c.answer('Noto‘g‘ri buyurtma.',show_alert=True)
 o=db.json_service_order(oid)
 if not o or o['status']!='pending':return await c.answer('Buyurtma topilmadi yoki yakunlangan.',show_alert=True)
 await state.update_data(deliver_json_service=oid)
 await state.set_state(AdminStates.deliver_json_service)
 await c.message.answer(f'📤 <b>#{oid}</b> uchun tayyorlangan <code>.json</code> faylni yuboring.',parse_mode='HTML')
 await c.answer()

@router.message(AdminStates.deliver_json_service,F.document)
async def jsdeliver_file(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();oid=int(d['deliver_json_service']);o=db.json_service_order(oid)
 if not o or o['status']!='pending':
  await state.clear();return await m.answer('❌ Buyurtma topilmadi yoki allaqachon yakunlangan.')
 name=(m.document.file_name or '').lower()
 if not name.endswith('.json'):
  return await m.answer('❌ Faqat .json fayl yuboring.')
 try:
  await m.bot.send_document(o['telegram_user_id'],m.document.file_id,
    caption=f'✅ <b>JSON #{oid} tayyor!</b>\n\n📦 Fayl tayyorlandi. Rahmat.',
    parse_mode='HTML')
 except Exception:
  return await m.answer('❌ Foydalanuvchiga yuborib bo‘lmadi. Buyurtma yopilmadi.')
 if not db.complete_json_service_order(oid,m.from_user.id):
  return await m.answer('⚠️ Fayl yuborildi, lekin buyurtma holatini yangilashda muammo bo‘ldi. Qayta yubormang, bazani tekshirish kerak.')
 await state.clear()
 await m.answer(f'✅ JSON #{oid} foydalanuvchiga yuborildi va buyurtma yakunlandi.',reply_markup=admin_menu())

@router.message(AdminStates.deliver_json_service)
async def jsdeliver_wrong(m:Message,config:Config):
 if not adm(m.from_user.id,config):return
 await m.answer('❌ Tayyor JSON faylini .json hujjat ko‘rinishida yuboring.')

@router.callback_query(F.data.startswith('jsreject:'))
async def jsreject(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(reject_json_service=int(c.data.split(':')[1]))
 await state.set_state(AdminStates.reject_json_service)
 await c.message.answer('❌ Buyurtmani rad etish sababini yuboring. Balans avtomatik qaytariladi.')
 await c.answer()

@router.message(AdminStates.reject_json_service,F.text)
async def jsreject_reason(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();o=db.reject_json_service_order(int(d['reject_json_service']),m.text[:500],True,m.from_user.id)
 await state.clear()
 if not o:return await m.answer('❌ Buyurtma topilmadi yoki allaqachon yakunlangan.')
 await m.answer(f'❌ JSON #{o["id"]} rad etildi. {format_money(o["price"])} balansga qaytarildi.',reply_markup=admin_menu())
 try:await m.bot.send_message(o['telegram_user_id'],f'❌ JSON tayyorlash buyurtmangiz #{o["id"]} rad etildi.\n💰 {format_money(o["price"])} balansingizga qaytarildi.\nSabab: {escape(o["reject_reason"])}',parse_mode='HTML')
 except Exception:pass

# ========================= BALANCE CARDS =========================
@router.callback_query(F.data=='adm:balancecards')
async def balancecards(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.balance_cards(False)
 text='💳 <b>BALANS TO‘LDIRISH KARTALARI</b>\n\n'
 text += ('\n'.join(f'{"🟢" if r["enabled"] else "🔴"} {escape(r["label"])} •••• {r["number"][-4:]}' for r in rows) if rows else 'Hali karta qo‘shilmagan.')
 await c.message.answer(text,parse_mode='HTML',reply_markup=balance_cards_admin(rows));await c.answer()

@router.callback_query(F.data=='bcardadd')
async def bcardadd(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.set_state(AdminStates.add_balance_card_label)
 await c.message.answer('➕ Karta nomini yuboring.\nMasalan: <b>Asosiy karta</b>',parse_mode='HTML');await c.answer()

@router.message(AdminStates.add_balance_card_label,F.text)
async def bcard_label(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 label=m.text.strip()[:80]
 if len(label)<2:return await m.answer('❌ Karta nomi juda qisqa.')
 await state.update_data(balance_card_label=label);await state.set_state(AdminStates.add_balance_card_number)
 await m.answer('💳 Karta raqamini yuboring (16–19 raqam).')

@router.message(AdminStates.add_balance_card_number,F.text)
async def bcard_number(m:Message,state:FSMContext,config:Config):
 if not adm(m.from_user.id,config):return
 import re
 n=re.sub(r'[\s-]','',m.text)
 if not n.isdigit() or not 16<=len(n)<=19:return await m.answer('❌ Karta raqami noto‘g‘ri. 16–19 raqam kiriting.')
 await state.update_data(balance_card_number=n);await state.set_state(AdminStates.add_balance_card_note)
 await m.answer('📝 Izoh/qo‘shimcha ma’lumot yuboring yoki <code>-</code> yozing.',parse_mode='HTML')

@router.message(AdminStates.add_balance_card_note,F.text)
async def bcard_note(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();note='' if m.text.strip()=='-' else m.text[:500]
 try:db.add_balance_card(d['balance_card_label'],d['balance_card_number'],note)
 except Exception:return await m.answer('❌ Bu karta allaqachon qo‘shilgan.')
 await state.clear();await m.answer('✅ Balans to‘ldirish kartasi qo‘shildi.',reply_markup=admin_menu())

@router.callback_query(F.data.startswith('bcard:'))
async def bcard(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.balance_card(int(c.data.split(':')[1]))
 if not r:return await c.answer('Karta topilmadi.',show_alert=True)
 await c.message.answer(f'💳 <b>{escape(r["label"])}</b>\n\nKarta: <code>{escape(r["number"])}</code>\n📝 {escape(r["note"] or "-")}\nStatus: {"🟢 ON" if r["enabled"] else "🔴 OFF"}',parse_mode='HTML',reply_markup=balance_card_manage(r));await c.answer()

@router.callback_query(F.data.startswith('bcardtoggle:'))
async def bcardtoggle(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 r=db.balance_card(int(c.data.split(':')[1]))
 if not r:return await c.answer('Karta topilmadi.',show_alert=True)
 db.update_balance_card(r['id'],enabled=not r['enabled']);await c.answer('Yangilandi.')
 await c.message.answer('💳 Balans kartalari',reply_markup=balance_cards_admin(db.balance_cards(False)))

@router.callback_query(F.data.startswith('bcarddelete:'))
async def bcarddelete(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 db.delete_balance_card(int(c.data.split(':')[1]));await c.answer('O‘chirildi.')
 await c.message.answer('💳 Balans kartalari',reply_markup=balance_cards_admin(db.balance_cards(False)))

# ========================= BALANCE TOPUPS =========================
@router.callback_query(F.data=='adm:topups')
async def topups(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 rows=db.pending_topups()
 if not rows:return await c.message.answer('💰 Kutilayotgan balans to‘ldirishlar yo‘q.',reply_markup=back_admin())
 for t in rows:
  uname=f'@{t["username"]}' if t['username'] else 'username yo‘q'
  text=(f'💰 <b>BALANS #{t["id"]}</b>\n👤 {escape(t["full_name"])}\n🔗 {escape(uname)}\n'
        f'🆔 <code>{t["telegram_user_id"]}</code>\n💰 Summa: <b>{format_money(t["amount"])}</b>\n'
        f'💳 Karta: {escape(t["card_label"])} •••• {t["card_number"][-4:]}\n🕐 {escape(t["created_at"])}\n📎 {escape(t["proof_type"])}')
  await c.message.answer(text,parse_mode='HTML',reply_markup=topup_actions(t['id']))
  try:
   if t['proof_type']=='photo':await c.message.answer_photo(t['proof'],caption=f'🧾 #{t["id"]}')
   elif t['proof_type']=='document':await c.message.answer_document(t['proof'],caption=f'🧾 #{t["id"]}')
   elif t['proof_type']=='text':await c.message.answer(f'🧾 <b>Isbot:</b>\n<pre>{escape(t["proof"])}</pre>',parse_mode='HTML')
  except Exception:pass
 await c.answer()

@router.callback_query(F.data.startswith('topupapprove:'))
async def topupapprove(c:CallbackQuery,db:Database,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 tid=int(c.data.split(':')[1]);t=db.review_topup(tid,True,admin_id=c.from_user.id,admin_username=c.from_user.username or '')
 if not t:return await c.answer('Bu to‘lov allaqachon ko‘rilgan.',show_alert=True)
 await c.message.edit_reply_markup(reply_markup=None)
 await c.message.answer(f'✅ Balans #{tid} tasdiqlandi: +{format_money(t["amount"])}')
 try:await c.bot.send_message(t['telegram_user_id'],f'✅ Balansingiz {format_money(t["amount"])} ga to‘ldirildi.\n💰 Yangi balans: {format_money(db.user(t["telegram_user_id"])["balance"])}')
 except Exception:pass
 await c.answer()

@router.callback_query(F.data.startswith('topupreject:'))
async def topupreject(c:CallbackQuery,state:FSMContext,config:Config):
 if not adm(c.from_user.id,config):return await deny(c)
 await state.update_data(reject_topup=int(c.data.split(':')[1]));await state.set_state(AdminStates.reject_topup)
 await c.message.answer('❌ Balans to‘ldirishni rad etish sababini yuboring.');await c.answer()

@router.message(AdminStates.reject_topup,F.text)
async def topupreject_reason(m:Message,state:FSMContext,db:Database,config:Config):
 if not adm(m.from_user.id,config):return
 d=await state.get_data();t=db.review_topup(int(d['reject_topup']),False,m.text[:500],m.from_user.id,m.from_user.username or '')
 await state.clear()
 if not t:return await m.answer('❌ To‘lov topilmadi yoki allaqachon ko‘rilgan.')
 await m.answer('❌ Balans to‘ldirish rad etildi.',reply_markup=admin_menu())
 try:await m.bot.send_message(t['telegram_user_id'],f'❌ Balans to‘ldirish #{t["id"]} rad etildi.\nSabab: {escape(t["reject_reason"])}',parse_mode='HTML')
 except Exception:pass

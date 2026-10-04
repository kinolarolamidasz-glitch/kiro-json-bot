from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

MENU = ['🛒 JSON sotish','📝 JSON tayyorlash','💰 Balansim','➕ Balans to‘ldirish','💸 Pul chiqarish','📦 Sotuvlarim','📜 Tarix','👤 Kabinet','💳 Kartalarim','❓ Yordam']

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛒 JSON sotish'), KeyboardButton(text='📝 JSON tayyorlash')],
            [KeyboardButton(text='💰 Balansim'), KeyboardButton(text='➕ Balans to‘ldirish')],
            [KeyboardButton(text='💸 Pul chiqarish'), KeyboardButton(text='📦 Sotuvlarim')],
            [KeyboardButton(text='📜 Tarix'), KeyboardButton(text='👤 Kabinet')],
            [KeyboardButton(text='💳 Kartalarim'), KeyboardButton(text='❓ Yordam')],
        ], resize_keyboard=True
    )

def plans(rows, prefix='plan'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{r['name']} — {r['price']:,}".replace(',',' '), callback_data=f"{prefix}:{r['id']}")] for r in rows
    ])

def payment_methods(rows, prefix='method'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=r['name'], callback_data=f'{prefix}:{r["id"]}')] for r in rows
    ])

def saved_cards(rows, prefix='cardpick'):
    buttons = [[InlineKeyboardButton(text=f"💳 {r['label']} •••• {r['number'][-4:]}", callback_data=f'{prefix}:{r["id"]}')] for r in rows]
    buttons.append([InlineKeyboardButton(text='➕ Yangi karta kiritish', callback_data=f'{prefix}:new')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cards_menu(rows):
    buttons = [[InlineKeyboardButton(text=f"💳 {r['label']} •••• {r['number'][-4:]}", callback_data=f'cardmanage:{r["id"]}')] for r in rows]
    buttons.append([InlineKeyboardButton(text='➕ Karta qo‘shish', callback_data='cardadd')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def card_manage(r):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 O‘chirish', callback_data=f'carddelete:{r["id"]}')],
        [InlineKeyboardButton(text='🔙 Kartalarim', callback_data='cards:home')]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Dashboard',callback_data='adm:stats')],
        [InlineKeyboardButton(text='📥 JSON Market',callback_data='adm:json'),InlineKeyboardButton(text='📝 JSON xizmat',callback_data='adm:jsonservice')],
        [InlineKeyboardButton(text='💎 Tariflar',callback_data='adm:plans'),InlineKeyboardButton(text='💳 To‘lov usullari',callback_data='adm:payments')],
        [InlineKeyboardButton(text='💸 Pul chiqarish',callback_data='adm:withdraw'),InlineKeyboardButton(text='💰 Balans to‘ldirish',callback_data='adm:topups')],
        [InlineKeyboardButton(text='👥 Foydalanuvchilar',callback_data='adm:users'),InlineKeyboardButton(text='💰 Balanslar',callback_data='adm:balances')],
        [InlineKeyboardButton(text='💳 Balans kartalari',callback_data='adm:balancecards')],
        [InlineKeyboardButton(text='📜 Tranzaksiyalar',callback_data='adm:transactions'),InlineKeyboardButton(text='📢 Kanallar',callback_data='adm:channels')],
        [InlineKeyboardButton(text='🔐 Majburiy obuna',callback_data='adm:membership'),InlineKeyboardButton(text='📣 Hammaga xabar',callback_data='adm:broadcast')],
        [InlineKeyboardButton(text='⚙️ Sozlamalar',callback_data='adm:settings'),InlineKeyboardButton(text='🗄 Backup',callback_data='adm:backup')]
    ])

def settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💸 Minimum withdrawal',callback_data='set:minwd')],
        [InlineKeyboardButton(text='❓ Help matni',callback_data='set:help')],
        [InlineKeyboardButton(text='📢 Official channel ID',callback_data='set:official_id'),InlineKeyboardButton(text='🔗 Official link',callback_data='set:official_link')],
        [InlineKeyboardButton(text='💳 Payment channel ID',callback_data='set:payment_channel')],
        [InlineKeyboardButton(text='🔐 Majburiy obuna ON/OFF',callback_data='set:membership')],
        [InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]
    ])


def cancel_inline():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Bekor qilish', callback_data='fsm:cancel')]])

def back_admin(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]])
def simple_back(cb): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Orqaga',callback_data=cb)]])

def submission_actions(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔄 PROCESSING',callback_data=f'jsonproc:{i}'),InlineKeyboardButton(text='✅ TASDIQLASH',callback_data=f'approve:{i}')],
        [InlineKeyboardButton(text='❌ RAD ETISH',callback_data=f'reject:{i}'),InlineKeyboardButton(text='📥 JSON',callback_data=f'download:{i}')],
        [InlineKeyboardButton(text='🗑 O‘CHIRISH',callback_data=f'delete:{i}')]
    ])

def withdrawal_actions(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔄 PROCESSING',callback_data=f'wdproc:{i}')],
        [InlineKeyboardButton(text='💸 TO‘LADIM',callback_data=f'paid:{i}'),InlineKeyboardButton(text='❌ RAD ETISH',callback_data=f'wreject:{i}')]
    ])

def plan_admin(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'🟢' if r['enabled'] else '🔴'} {r['name']} — {r['price']:,}".replace(',',' '),callback_data=f'planadm:{r["id"]}')] for r in rows
    ]+[[InlineKeyboardButton(text='➕ Tarif qo‘shish',callback_data='planadd')],[InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]])

def plan_manage(r):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Narx',callback_data=f'planprice:{r["id"]}'),InlineKeyboardButton(text=('🔴 O‘chirish' if r['enabled'] else '🟢 Yoqish'),callback_data=f'plantoggle:{r["id"]}')],
        [InlineKeyboardButton(text='🗑 O‘chirish',callback_data=f'plandelete:{r["id"]}')],[InlineKeyboardButton(text='🔙 Tariflar',callback_data='adm:plans')]
    ])

def pay_admin(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'🟢' if r['enabled'] else '🔴'} {r['name']}",callback_data=f'payadm:{r["id"]}')] for r in rows
    ]+[[InlineKeyboardButton(text='➕ To‘lov usuli qo‘shish',callback_data='payadd')],[InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]])

def pay_manage(r):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Rekvizit',callback_data=f'paydetails:{r["id"]}'),InlineKeyboardButton(text='📝 Izoh',callback_data=f'paynote:{r["id"]}')],
        [InlineKeyboardButton(text=('🔴 O‘chirish' if r['enabled'] else '🟢 Yoqish'),callback_data=f'paytoggle:{r["id"]}'),InlineKeyboardButton(text='🗑 O‘chirish',callback_data=f'paydelete:{r["id"]}')],
        [InlineKeyboardButton(text='🔙 To‘lovlar',callback_data='adm:payments')]
    ])


def required_chat_admin(rows):
    buttons=[]
    for r in rows:
        status='🟢' if r['enabled'] else '🔴'
        buttons.append([InlineKeyboardButton(text=f'{status} {r["title"][:45]}', callback_data=f'mchat:{r["id"]}')])
    buttons.append([InlineKeyboardButton(text='➕ Kanal/guruh qo‘shish', callback_data='mchatadd')])
    buttons.append([InlineKeyboardButton(text='🔐 ON/OFF', callback_data='set:membership')])
    buttons.append([InlineKeyboardButton(text='🔙 Admin panel', callback_data='adm:home')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def required_chat_manage(r):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=('🔴 O‘chirish' if r['enabled'] else '🟢 Yoqish'), callback_data=f'mchattoggle:{r["id"]}')],
        [InlineKeyboardButton(text='🗑 O‘chirish', callback_data=f'mchatdelete:{r["id"]}')],
        [InlineKeyboardButton(text='🔙 Majburiy obuna', callback_data='adm:membership')]
    ])


def balance_cards_admin(rows):
    buttons=[[InlineKeyboardButton(text=f"{'🟢' if r['enabled'] else '🔴'} {r['label']} •••• {r['number'][-4:]}",callback_data=f"bcard:{r['id']}")] for r in rows]
    buttons += [[InlineKeyboardButton(text='➕ Karta qo‘shish',callback_data='bcardadd')],
                [InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def balance_card_manage(r):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=('🔴 O‘chirish' if r['enabled'] else '🟢 Yoqish'),callback_data=f'bcardtoggle:{r["id"]}')],
        [InlineKeyboardButton(text='🗑 O‘chirish',callback_data=f'bcarddelete:{r["id"]}')],
        [InlineKeyboardButton(text='🔙 Balans kartalari',callback_data='adm:balancecards')]
    ])

def topup_cards(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'💳 {r["label"]} •••• {r["number"][-4:]}',callback_data=f'topupcard:{r["id"]}')] for r in rows
    ] + [[InlineKeyboardButton(text='❌ Bekor qilish',callback_data='fsm:cancel')]])

def topup_actions(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ TASDIQLASH',callback_data=f'topupapprove:{i}'),
         InlineKeyboardButton(text='❌ RAD ETISH',callback_data=f'topupreject:{i}')],
        [InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]
    ])

def json_service_admin_actions(i):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📤 JSON yuborish',callback_data=f'jsdeliver:{i}'),
         InlineKeyboardButton(text='❌ RAD + REFUND',callback_data=f'jsreject:{i}')],
        [InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]
    ])

def json_service_price_admin(price):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Narxni o‘zgartirish',callback_data='jsprice')],
        [InlineKeyboardButton(text='🔙 Admin panel',callback_data='adm:home')]
    ])

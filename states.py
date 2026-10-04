from aiogram.fsm.state import State, StatesGroup

class SellStates(StatesGroup):
    waiting_json = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()
    waiting_card = State()
    waiting_recipient = State()

class TopupStates(StatesGroup):
    waiting_amount = State()
    waiting_proof = State()

class JsonServiceStates(StatesGroup):
    waiting_request = State()

class CardStates(StatesGroup):
    waiting_number = State()
    waiting_name = State()

class AdminStates(StatesGroup):
    reject_json = State()
    reject_withdrawal = State()
    add_plan_name = State()
    add_plan_price = State()
    edit_plan_price = State()
    add_payment_name = State()
    add_payment_details = State()
    add_payment_note = State()
    edit_payment_details = State()
    edit_payment_note = State()
    set_value = State()
    balance_user = State()
    balance_amount = State()
    balance_note = State()
    broadcast = State()
    add_balance_card_label = State()
    add_balance_card_number = State()
    add_balance_card_note = State()
    json_service_price = State()
    deliver_json_service = State()
    reject_json_service = State()
    reject_topup = State()
    add_required_chat_id = State()
    add_required_chat_link = State()

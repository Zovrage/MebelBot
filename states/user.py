from aiogram.fsm.state import StatesGroup, State

# Состояния для оформления заказа пользователем
class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_comment = State()


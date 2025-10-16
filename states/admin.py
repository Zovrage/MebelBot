from aiogram.fsm.state import StatesGroup, State

class ProductForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_subcategory = State()
    waiting_for_country = State()
    waiting_for_type = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_sizes = State()
    waiting_for_images = State()

class EditProductForm(StatesGroup):
    waiting_for_field = State()
    waiting_for_value = State()

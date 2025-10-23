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
    waiting_for_step = State()  # Для пошагового добавления
    waiting_for_value = State() # Для ввода значения шага
    waiting_for_final_confirm = State() # Для финального подтверждения

class EditProductForm(StatesGroup):
    waiting_for_field = State()
    waiting_for_value = State()
    waiting_for_photo = State()

class ManageProductFilter(StatesGroup):
    waiting_for_category = State()
    waiting_for_country = State()
    waiting_for_type = State()
    viewing_product = State()
    waiting_for_filter = State() # Для фильтрации товаров

from aiogram.fsm.state import StatesGroup, State

# Состояния для добавления нового товара
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

# Состояния для редактирования товара
class EditProductForm(StatesGroup):
    waiting_for_field = State()
    waiting_for_value = State()

# Состояния для фильтрации товаров в админке
class AdminProductFilter(StatesGroup):
    waiting_for_category = State()
    waiting_for_country = State()
    waiting_for_type = State()

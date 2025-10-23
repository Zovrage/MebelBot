from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню для админа
admin_main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="🗂️ Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton(text="📋 Заявки (лиды)", callback_data="leads")],
        [InlineKeyboardButton(text="🏠 На главное меню", callback_data="back_main")],
    ]
)

# Общая функция вывода списка товаров (если используется вне управления)
def get_products_kb(products):
    kb = InlineKeyboardMarkup()
    for product in products:
        kb.add(InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}"))
    return kb

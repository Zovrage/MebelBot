from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Клавиатура управления отдельным товаром
def get_product_manage_kb(product_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{product_id}"),
             InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{product_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_back_to_category")]
        ]
    )

# Клавиатура управления списком товаров с пагинацией
def get_products_manage_kb(products, page, total_pages):
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=f"{product['name']} (ID: {product['id']})",
            callback_data=f"manage_product_{product['id']}"
        )
        kb.button(
            text="✏️ Редактировать",
            callback_data=f"edit_product_{product['id']}"
        )
        kb.button(
            text="🗑️ Удалить",
            callback_data=f"delete_product_{product['id']}"
        )
    nav_row = []
    if page > 1:
        nav_row.append({"text": "🔙 Назад", "callback_data": f"manage_products_page_{page-1}"})
    if page < total_pages:
        nav_row.append({"text": "Вперёд ➡️", "callback_data": f"manage_products_page_{page+1}"})
    if nav_row:
        kb.row(*[InlineKeyboardButton(**btn) for btn in nav_row])
    kb.button(text="🏠 На главное меню", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

# Клавиатура выбора категории для управления товарами
def get_manage_category_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🛏️ Спальная мебель", callback_data="manage_category_bedroom")],
            [InlineKeyboardButton(text=f"🍽️ Кухонная мебель", callback_data="manage_category_kitchen")],
            [InlineKeyboardButton(text=f"🛋️ Мягкая мебель", callback_data="manage_category_soft")],
            [InlineKeyboardButton(text=f"🪑 Столы и стулья", callback_data="manage_category_tables")],
            [InlineKeyboardButton(text=f"🗄️ Тумбы и комоды", callback_data="manage_category_dressers")],
            [InlineKeyboardButton(text=f"🛌 Кровать", callback_data="manage_category_bed")],
            [InlineKeyboardButton(text=f"🛌 Матрасы", callback_data="manage_category_mattress")],
            [InlineKeyboardButton(text=f"🚪 Шкафы", callback_data="manage_category_wardrobe")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_back_to_admin")],
        ]
    )

# Клавиатура для редактирования полей товара
def get_edit_fields_kb(fields):
    kb = [
        [InlineKeyboardButton(text=label, callback_data=f"editfield_{field}")]
        for field, label in fields
    ]
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_edit_back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

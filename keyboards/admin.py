from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import ProductCategory, LeadStatus



# Главное меню для админа
admin_main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="🗂️ Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton(text="📋 Заявки (лиды)", callback_data="leads")],
        [InlineKeyboardButton(text="🏠 На главное меню", callback_data="back_main")],
    ]
)



# Клавиатура выбора категории товара (emoji прямо в тексте)
def get_category_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🛏️ Спальная мебель", callback_data="category_bedroom")],
            [InlineKeyboardButton(text=f"🍽️ Кухонная мебель", callback_data="category_kitchen")],
            [InlineKeyboardButton(text=f"🛋️ Мягкая мебель", callback_data="category_soft")],
            [InlineKeyboardButton(text=f"🪑 Столы и стулья", callback_data="category_tables")],
            [InlineKeyboardButton(text=f"🗄️ Тумбы и комоды", callback_data="category_dressers")],
            [InlineKeyboardButton(text=f"🛌 Кровать", callback_data="category_bed")],
            [InlineKeyboardButton(text=f"🛌 Матрасы", callback_data="category_mattress")],
            [InlineKeyboardButton(text=f"🚪 Шкафы", callback_data="category_wardrobe")],
        ]
    )

# Клавиатура выбора страны с emoji
def get_country_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Российская", callback_data="country_russia")],
            [InlineKeyboardButton(text="🇹🇷 Турецкая", callback_data="country_turkey")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="country_skip_country")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="country_cancel_country")],
        ]
    )

# Клавиатура выбора типа с emoji
def get_type_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Прямая", callback_data="type_straight")],
            [InlineKeyboardButton(text="↩️ Угловая", callback_data="type_corner")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="type_skip_type")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="type_cancel_type")],
        ]
    )

# Клавиатура статусов лида
lead_status_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=status.value, callback_data=f"lead_status_{status.name}")]
        for status in LeadStatus
    ]
)

def get_products_kb(products):
    kb = InlineKeyboardMarkup()
    for product in products:
        kb.add(InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}"))
    return kb

def get_product_manage_kb(product_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{product_id}"),
             InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{product_id}")]
        ]
    )

def get_leads_kb(leads):
    kb = InlineKeyboardMarkup()
    for lead in leads:
        kb.add(InlineKeyboardButton(text=f"{lead.name} ({lead.status.value})", callback_data=f"lead_{lead.id}"))
    return kb

def get_lead_manage_kb(lead_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить статус", callback_data=f"change_status_{lead_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_lead_{lead_id}")]
        ]
    )

def get_add_step_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="add_skip"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="add_cancel")]
        ]
    )

def get_edit_fields_kb(fields):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"editfield_{field}")]
            for field, label in fields
        ]
    )

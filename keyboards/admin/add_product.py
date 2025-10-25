from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура выбора категории товара
def get_category_kb():
    kb = ([
        [InlineKeyboardButton(text=f"🛏️ Спальная мебель", callback_data="category_bedroom")],
        [InlineKeyboardButton(text=f"🍽️ Кухонная мебель", callback_data="category_kitchen")],
        [InlineKeyboardButton(text=f"🛋️ Мягкая мебель", callback_data="category_soft")],
        [InlineKeyboardButton(text=f"🪑 Столы и стулья", callback_data="category_tables")],
        [InlineKeyboardButton(text=f"🗄️ Тумбы и комоды", callback_data="category_dressers")],
        [InlineKeyboardButton(text=f"🛌 Кровать", callback_data="category_bed")],
        [InlineKeyboardButton(text=f"🛌 Матрасы", callback_data="category_mattress")],
        [InlineKeyboardButton(text=f"🚪 Шкафы", callback_data="category_wardrobe")],
    ])
    kb.append([
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="add_skip"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="add_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавиатура выбора страны с emoji
def get_country_kb():
    buttons = [
        [InlineKeyboardButton(text="🇷🇺 Российская", callback_data="country_russia")],
        [InlineKeyboardButton(text="🇹🇷 Турецкая", callback_data="country_turkey")],
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="country_skip_country"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="country_cancel_country")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура выбора типа
def get_type_kb():
    buttons = [
        [InlineKeyboardButton(text="➡️ Прямая", callback_data="type_straight")],
        [InlineKeyboardButton(text="↩️ Угловая", callback_data="type_corner")],
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="type_skip_type"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="type_cancel_type")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для фото

def get_images_done_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Готово", callback_data="images_done"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="add_cancel")]
        ]
    )

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import ProductCategory

def get_admin_main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Добавить товар', callback_data='admin_add_product')
    kb.button(text='🛠️ Управление товарами', callback_data='admin_manage_products')
    kb.button(text='📋 Заявки (лиды)', callback_data='admin_leads')
    kb.adjust(1)
    return kb.as_markup()

def get_product_manage_kb(product_id):
    kb = InlineKeyboardBuilder()
    kb.button(text='✏️ Редактировать', callback_data=f'admin_edit_{product_id}')
    kb.button(text='🗑️ Удалить', callback_data=f'admin_delete_{product_id}')
    kb.button(text='🔙 Назад', callback_data='admin_back_main')
    kb.adjust(1)
    return kb.as_markup()

def get_lead_manage_kb(lead_id, status):
    kb = InlineKeyboardBuilder()
    if status != 'Новая':
        kb.button(text='🆕 Сделать новой', callback_data=f'lead_status_{lead_id}_new')
    if status != 'В работе':
        kb.button(text='🏃 В работу', callback_data=f'lead_status_{lead_id}_in_progress')
    if status != 'Закрыта':
        kb.button(text='✅ Закрыть', callback_data=f'lead_status_{lead_id}_closed')
    kb.button(text='🗑️ Удалить', callback_data=f'lead_delete_{lead_id}')
    kb.button(text='🔙 Назад', callback_data='admin_leads')
    kb.adjust(1)
    return kb.as_markup()

def get_back_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад', callback_data='admin_back_main')]])

def get_edit_product_kb(product_id):
    kb = InlineKeyboardBuilder()
    kb.button(text='✏️ Название', callback_data=f'edit_name_{product_id}')
    kb.button(text='🗂️ Категория', callback_data=f'edit_category_{product_id}')
    kb.button(text='📝 Описание', callback_data=f'edit_description_{product_id}')
    kb.button(text='📏 Размеры', callback_data=f'edit_sizes_{product_id}')
    kb.button(text='🖼️ Фото', callback_data=f'edit_images_{product_id}')
    kb.button(text='💰 Цена', callback_data=f'edit_price_{product_id}')
    kb.button(text='🔙 Назад', callback_data='admin_manage_products')
    kb.adjust(1)
    return kb.as_markup()

def get_admin_categories_kb():
    from database.models import ProductCategory
    kb = InlineKeyboardBuilder()
    emoji_map = {
        'bedroom': '🛏️',
        'kitchen': '🍽️',
        'soft': '🛋️',
        'tables': '🪑',
        'dressers': '🗄️',
        'mattress': '🛌',
        'wardrobe': '🚪',
    }
    for cat in ProductCategory:
        emoji = emoji_map.get(cat.name, '')
        kb.button(text=f'{emoji} {cat.value}', callback_data=f'admin_cat_{cat.name}')
    kb.button(text='🔙 Назад', callback_data='admin_back_main')
    kb.adjust(1)
    return kb.as_markup()

def get_admin_countries_kb(category):
    kb = InlineKeyboardBuilder()
    kb.button(text='🇷🇺 Российская', callback_data=f'admin_country_{category}_Российская')
    kb.button(text='🇹🇷 Турецкая', callback_data=f'admin_country_{category}_Турецкая')
    kb.button(text='🔙 Назад', callback_data=f'back_to_category')
    kb.adjust(1)
    return kb.as_markup()

def get_admin_types_kb(category, country):
    kb = InlineKeyboardBuilder()
    if category in ['kitchen', 'soft'] and (country is None or country == 'Российская'):
        kb.button(text='➡️ прямая', callback_data=f'admin_type_{category}_{country}_прямая')
        kb.button(text='↩️ угловая', callback_data=f'admin_type_{category}_{country}_угловая')
    if category == 'kitchen':
        kb.button(text='🔙 Назад', callback_data='back_to_category')
    else:
        kb.button(text='🔙 Назад', callback_data=f'back_to_country_{category}')
    kb.adjust(1)
    return kb.as_markup()

def get_add_product_step_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⏭️ Пропустить', callback_data='skip_add')
    kb.button(text='❌ Отмена', callback_data='cancel_add')
    kb.adjust(1)
    return kb.as_markup()

def get_edit_product_step_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='⏭️ Пропустить', callback_data='skip_edit')
    kb.button(text='❌ Отмена', callback_data='cancel_edit')
    kb.adjust(1)
    return kb.as_markup()

def get_categories_kb():
    kb = InlineKeyboardBuilder()
    for cat in ProductCategory:
        print(f'Добавляю кнопку категории: {cat.value} ({cat.name})')  # DEBUG
        kb.button(text=cat.value, callback_data=f'admin_cat_{cat.name}')
    kb.adjust(1)
    markup = kb.as_markup()
    print(f'Клавиатура категорий: {markup}')  # DEBUG
    return markup

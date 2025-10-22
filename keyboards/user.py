from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛏️ Спальная мебель', callback_data='cat_bedroom')],
    [InlineKeyboardButton(text='🍽️ Кухонная мебель', callback_data='cat_kitchen')],
    [InlineKeyboardButton(text='🛋️ Мягкая мебель', callback_data='cat_soft')],
    [InlineKeyboardButton(text='🪑 Столы и стулья', callback_data='cat_tables')],
    [InlineKeyboardButton(text='🗄️ Тумбы и комоды', callback_data='cat_dressers')],
    [InlineKeyboardButton(text='🛌 Кровати', callback_data='cat_beds')],
    [InlineKeyboardButton(text='🛌 Матрасы', callback_data='cat_mattress')],
    [InlineKeyboardButton(text='🚪 Шкафы', callback_data='cat_wardrobe')],
    [InlineKeyboardButton(text='ℹ️ О компании / Контакты', callback_data='about')],
    [InlineKeyboardButton(text='⚙️ Настройка бота', callback_data='admin_panel')],
])

def get_bedroom_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🇷🇺 Российская', callback_data='bedroom_rus')
    kb.button(text='🇹🇷 Турецкая', callback_data='bedroom_tur')
    kb.button(text='🔙 Назад', callback_data='back_main')
    kb.adjust(1)
    return kb.as_markup()

def get_kitchen_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➡️ Прямая', callback_data='kitchen_straight')
    kb.button(text='↩️ Угловая', callback_data='kitchen_corner')
    kb.button(text='🔙 Назад', callback_data='back_main')
    kb.adjust(1)
    return kb.as_markup()

def get_soft_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='🇷🇺 Российская', callback_data='soft_rus')
    kb.button(text='🇹🇷 Турецкая', callback_data='soft_tur')
    kb.button(text='🔙 Назад', callback_data='back_main')
    kb.adjust(1)
    return kb.as_markup()

def get_soft_rus_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➡️ Прямая', callback_data='soft_rus_straight')
    kb.button(text='↩️ Угловая', callback_data='soft_rus_corner')
    kb.button(text='🔙 Назад', callback_data='soft')
    kb.adjust(1)
    return kb.as_markup()

def get_simple_cat_kb(back_cb):
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data=back_cb)
    kb.adjust(1)
    return kb.as_markup()

def get_product_card_kb(product_id):
    kb = InlineKeyboardBuilder()
    kb.button(text='❓ Задать вопрос', callback_data=f'ask_{product_id}')
    kb.button(text='📞 Заказать консультацию', callback_data=f'consult_{product_id}')
    kb.button(text='🛒 Оформить заказ', callback_data=f'order_{product_id}')
    kb.button(text='🔙 Назад', callback_data='back_to_cat')
    kb.adjust(1)
    return kb.as_markup()

def get_gallery_nav_kb(product_ids, current_idx):
    kb = InlineKeyboardBuilder()
    if current_idx > 0:
        kb.button(text='⏮️ Предыдущий', callback_data=f'gallery_{product_ids[current_idx-1]}')
    if current_idx < len(product_ids) - 1:
        kb.button(text='⏭️ Следующий', callback_data=f'gallery_{product_ids[current_idx+1]}')
    kb.button(text='🔙 Назад', callback_data='back_to_cat')
    kb.adjust(1)
    return kb.as_markup()

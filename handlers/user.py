import re
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputFile
from aiogram.types.input_file import FSInputFile

from database.crud import get_products, add_lead, get_photos_by_product
from database.models import ProductCategory
from database.db import async_session
from states.user import OrderForm
from keyboards.user import (
    main_menu_kb, get_bedroom_kb, get_kitchen_kb, get_soft_kb, get_soft_rus_kb,
    get_simple_cat_kb, get_product_card_kb
)



router = Router()

# --- Главное меню ---
@router.message(F.text == '/start')
async def start_menu(msg: Message):
    text = (
        "✨ Добро пожаловать в MebelBot! ✨\n\n"
        "🏠 Здесь вы найдёте мебель для дома и офиса:\n"
        "   • Спальни 🛏️\n"
        "   • Кухни 🍽️\n"
        "   • Мягкая мебель 🛋️\n"
        "   • Шкафы, столы и многое другое!\n\n"
        "💬 Вы можете:\n"
        "   • Посмотреть каталог товаров\n"
        "   • Оставить заявку на покупку\n"
        "   • Получить консультацию\n"
        "   • Задать вопрос менеджеру\n\n"
        "📲 Просто выберите нужную категорию ниже!\n\n"
        "Спасибо, что выбрали нас! Если возникнут вопросы — мы всегда на связи."
    )
    await msg.answer(text, reply_markup=main_menu_kb)

@router.callback_query(F.data == 'back_main')
async def back_main(call: CallbackQuery, state: FSMContext = None):
    # Удаляем сообщения-карточки, если они есть
    error = False
    if state is not None:
        data = await state.get_data()
        msg_ids = data.get('product_message_ids', [])
        for msg_id in msg_ids:
            try:
                await call.bot.delete_message(call.message.chat.id, msg_id)
            except Exception:
                pass
        await state.update_data(product_message_ids=[])
    try:
        await call.message.edit_text('Главное меню. Выберите категорию:', reply_markup=main_menu_kb)
    except Exception:
        error = True
    if error:
        await call.message.answer('Главное меню. Выберите категорию:', reply_markup=main_menu_kb)

@router.callback_query(F.data == 'back_to_cat')
async def back_to_cat(call: CallbackQuery, state: FSMContext = None):
    # Удаляем сообщения-карточки, если они есть
    error = False
    if state is not None:
        data = await state.get_data()
        msg_ids = data.get('product_message_ids', [])
        for msg_id in msg_ids:
            try:
                await call.bot.delete_message(call.message.chat.id, msg_id)
            except Exception:
                pass
        await state.update_data(product_message_ids=[])
    try:
        await call.message.edit_text('Выберите категорию:', reply_markup=main_menu_kb)
    except Exception:
        error = True
    if error:
        await call.message.answer('Выберите категорию:', reply_markup=main_menu_kb)

# --- Категории и подкатегории ---
@router.callback_query(F.data == 'cat_bedroom')
async def bedroom_menu(call: CallbackQuery):
    await call.message.edit_text('Спальная мебель:', reply_markup=get_bedroom_kb())

@router.callback_query(F.data == 'cat_kitchen')
async def kitchen_menu(call: CallbackQuery):
    await call.message.edit_text('Кухонная мебель:', reply_markup=get_kitchen_kb())

@router.callback_query(F.data == 'cat_soft')
async def soft_menu(call: CallbackQuery):
    await call.message.edit_text('Мягкая мебель:', reply_markup=get_soft_kb())

@router.callback_query(F.data == 'soft')
async def soft_menu_back(call: CallbackQuery):
    await call.message.edit_text('Мягкая мебель:', reply_markup=get_soft_kb())

@router.callback_query(F.data == 'soft_rus')
async def soft_rus_menu(call: CallbackQuery):
    await call.message.edit_text('Мягкая мебель — Российская:', reply_markup=get_soft_rus_kb())

@router.callback_query(F.data == 'back_to_cat')
async def back_to_cat(call: CallbackQuery, state: FSMContext = None):
    # Удаляем сообщения-карточки, если они есть
    error = False
    if state is not None:
        data = await state.get_data()
        msg_ids = data.get('product_message_ids', [])
        for msg_id in msg_ids:
            try:
                await call.bot.delete_message(call.message.chat.id, msg_id)
            except Exception:
                pass
        await state.update_data(product_message_ids=[])
    try:
        await call.message.edit_text('Выберите категорию:', reply_markup=main_menu_kb)
    except Exception:
        error = True
    if error:
        await call.message.answer('Выберите категорию:', reply_markup=main_menu_kb)

# --- Галерея товаров по категориям ---
def get_country_display(country_code):
    if country_code == 'russia':
        return '🇷🇺 Российская'
    elif country_code == 'turkey':
        return '🇹🇷 Турецкая'
    return country_code or '-'

def get_type_display(type_code):
    if type_code == 'straight':
        return 'Прямая'
    elif type_code == 'corner':
        return 'Угловая'
    return type_code or '-'

async def show_products(call, category, country=None, type_=None, state: FSMContext = None):
    # Удаляем предыдущие сообщения с товарами (если есть)
    if state is not None:
        data = await state.get_data()
        prev_product_msgs = data.get('product_message_ids', [])
        for msg_id in prev_product_msgs:
            try:
                await call.bot.delete_message(call.message.chat.id, msg_id)
            except Exception:
                pass
        await state.update_data(product_message_ids=[])
    else:
        # fallback: удаляем только текущее сообщение, если не используем FSM
        try:
            await call.message.delete()
        except Exception:
            pass
    async with async_session() as session:
        # Исправление: если type_ == "skip_type" или пустая строка, не фильтруем по типу
        type_for_query = None if type_ in ("skip_type", "", None) else type_
        products = await get_products(session, category=category, country=country, type_=type_for_query)
        if not products:
            if call.message:
                try:
                    await call.message.edit_text('Товаров нет', reply_markup=get_simple_cat_kb('back_main'))
                except Exception:
                    await call.message.answer('Товаров нет', reply_markup=get_simple_cat_kb('back_main'))
            else:
                await call.message.answer('Товаров нет', reply_markup=get_simple_cat_kb('back_main'))
            return
        new_product_msgs = []
        for idx, product in enumerate(products):
            # Получаем фото из таблицы Photo
            photos = await get_photos_by_product(session, product.id)
            media = []
            for i, photo in enumerate(photos):
                file_path = os.path.join('media', photo.filename)
                if os.path.exists(file_path):
                    media.append(InputMediaPhoto(media=FSInputFile(file_path), caption=None))
            price = product.price
            if price is None or price == 0:
                price_str = '-'
            else:
                price_str = f"{int(price) if float(price).is_integer() else price} ₽"
            card_text = (
                f"Название: {product.name}\n"
                f"Описание: {product.description or '-'}\n"
                f"Страна: {get_country_display(product.country)}\n"
                f"Тип: {get_type_display(getattr(product, 'type', None))}\n"
                f"Размеры: {getattr(product, 'sizes', '-') or '-'}\n"
                f"Цена: {price_str}"
            )
            # 1. Сначала фото
            if media:
                if len(media) == 1:
                    msg = await call.message.answer_photo(media=media[0].media)
                    new_product_msgs.append(msg.message_id)
                else:
                    msgs = await call.message.answer_media_group(media)
                    for m in msgs:
                        new_product_msgs.append(m.message_id)
            # 2. Затем карточка товара отдельным сообщением
            msg_card = await call.message.answer(card_text, parse_mode='HTML')
            new_product_msgs.append(msg_card.message_id)
            # 3. Затем кнопки отдельным сообщением
            msg_btns = await call.message.answer("Выберите действие:", reply_markup=get_product_card_kb(product.id))
            new_product_msgs.append(msg_btns.message_id)
    # Сохраняем id новых сообщений в FSM для последующего удаления
    if state is not None:
        await state.update_data(product_message_ids=new_product_msgs)

# --- Карточка товара ---
@router.callback_query(F.data.startswith('bedroom'))
async def show_bedroom(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    sub = call.data.replace('bedroom_', '')
    country = None
    if sub in ['rus', 'tur']:
        country = 'russia' if sub == 'rus' else 'turkey'
    await show_products(call, ProductCategory.bedroom, country=country, state=state)

@router.callback_query(F.data.startswith('kitchen'))
async def show_kitchen(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    sub = call.data.replace('kitchen_', '')
    type_ = None
    if sub in ['straight', 'corner']:
        type_ = sub  # 'straight' или 'corner'
    await show_products(call, ProductCategory.kitchen, type_=type_, state=state)

@router.callback_query(F.data == 'soft_rus_straight')
async def show_soft_rus_straight(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.soft, country='russia', type_='straight', state=state)

@router.callback_query(F.data == 'soft_rus_corner')
async def show_soft_rus_corner(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.soft, country='russia', type_='corner', state=state)

@router.callback_query(F.data == 'soft_tur')
async def show_soft_tur(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.soft, country='turkey', state=state)

@router.callback_query(F.data == 'cat_tables')
async def show_tables(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.tables, state=state)

@router.callback_query(F.data == 'cat_dressers')
async def show_dressers(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.dressers, state=state)

@router.callback_query(F.data == 'cat_mattress')
async def show_mattress(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.mattress, state=state)

@router.callback_query(F.data == 'cat_wardrobe')
async def show_wardrobe(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.wardrobe, state=state)

@router.callback_query(F.data == 'cat_beds')
async def show_beds(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await show_products(call, ProductCategory.beds, state=state)

# --- О компании ---
@router.callback_query(F.data == 'about')
async def about_company(call: CallbackQuery):
    await call.message.edit_text('Мебельный магазин. Контакты: +7-900-000-00-00\nАдрес: г. Пример, ул. Мебельная, 1', reply_markup=get_simple_cat_kb('back_main'))

# --- Заказ, консультация, вопрос ---
@router.callback_query(F.data.startswith('order_'))
async def order_start(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split('_')[1])
    await state.update_data(product_id=product_id)
    await call.message.answer('Введите ваше имя:')
    await state.set_state(OrderForm.waiting_for_name)

@router.message(OrderForm.waiting_for_name)
async def order_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer('Введите телефон (например, +79991234567):')
    await state.set_state(OrderForm.waiting_for_phone)

@router.message(OrderForm.waiting_for_phone)
async def order_phone(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    if not re.match(r'^\+?7\d{10}$', phone):
        await msg.answer('Некорректный формат телефона. Введите в формате +79991234567:')
        return
    await state.update_data(phone=phone)
    await msg.answer('Комментарий (опционально, или напишите "-")')
    await state.set_state(OrderForm.waiting_for_comment)

@router.message(OrderForm.waiting_for_comment)
async def order_comment(msg: Message, state: FSMContext):
    data = await state.get_data()
    comment = msg.text if msg.text != '-' else ''
    async with async_session() as session:
        await add_lead(session, name=data['name'], phone=data['phone'], product_id=data['product_id'], comment=comment)
    await msg.answer('Спасибо! Ваша заявка отправлена менеджеру. Мы свяжемся с вами.')
    await state.clear()

# --- Кнопки "Задать вопрос" и "Заказать консультацию" ---
@router.callback_query(F.data.startswith('ask_'))
async def ask_question(call: CallbackQuery):
    await call.message.answer('Пожалуйста, напишите ваш вопрос. Менеджер свяжется с вами.')

@router.callback_query(F.data.startswith('consult_'))
async def consult_request(call: CallbackQuery):
    await call.message.answer('Пожалуйста, отправьте ваш телефон для консультации.')

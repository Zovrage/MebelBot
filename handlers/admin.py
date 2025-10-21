import os
import uuid
import urllib.parse

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from keyboards.admin import get_admin_main_kb, get_categories_kb, get_admin_countries_kb, get_admin_types_kb, get_back_admin_kb, get_admin_categories_kb, get_product_manage_kb, get_fsm_cancel_skip_kb
from keyboards.user import main_menu_kb
from config import ADMIN_IDS
from database.crud import add_product, get_photos_by_product
from database.models import ProductCategory
from database.db import async_session
from states.admin import ProductForm




router = Router()

# --- Проверка администратора ---
def is_admin(user_id):
    return user_id in ADMIN_IDS


def safe_edit_text(message, new_text, new_markup=None):
    """
    Безопасное редактирование текста сообщения с обработкой ошибок TelegramBadRequest.
    """
    try:
        current_text = message.text
        current_markup = message.reply_markup
        markup_changed = False
        if current_markup is not None and new_markup is not None:
            try:
                markup_changed = current_markup.model_dump() != new_markup.model_dump()
            except Exception:
                markup_changed = current_markup != new_markup
        elif current_markup != new_markup:
            markup_changed = True
        if current_text != new_text or markup_changed:
            return message.edit_text(new_text, reply_markup=new_markup)
        elif markup_changed:
            return message.edit_reply_markup(reply_markup=new_markup)
    except TelegramBadRequest as e:
        if 'message to edit not found' in str(e):
            return message.answer('Сообщение не найдено или уже удалено.', reply_markup=new_markup)
        elif 'message is not modified' in str(e):
            pass  # Игнорируем, если текст не изменился
        else:
            import logging
            logging.exception(f'Ошибка при редактировании сообщения: {e}')
    return None

@router.callback_query(F.data == 'admin_back_main')
async def admin_back_main(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    new_text = 'Админ-панель'
    new_markup = get_admin_main_kb()
    await safe_edit_text(call.message, new_text, new_markup)

# --- Добавление товара отключено ---
@router.callback_query(F.data == 'admin_add_product')
async def admin_add_product(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    await state.clear()
    await state.set_state(ProductForm.waiting_for_name)
    await call.message.edit_text(
        'Этап 1/7\nВведите название товара:',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_name)
async def process_product_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await state.set_state(ProductForm.waiting_for_category)
    await message.answer(
        'Этап 2/7\nВыберите категорию товара:',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_category)
async def process_product_category(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(category=message.text)
    await state.set_state(ProductForm.waiting_for_subcategory)
    await message.answer(
        'Этап 2.1/7\nВведите подкатегорию товара (или пропустите):',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_subcategory)
async def process_product_subcategory(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(subcategory=message.text)
    await state.set_state(ProductForm.waiting_for_country)
    await message.answer(
        'Этап 3/7\nВведите страну производства:',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_country)
async def process_product_country(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(country=message.text)
    await state.set_state(ProductForm.waiting_for_type)
    await message.answer(
        'Этап 4/7\nВведите тип (прямая, угловая и т.п.):',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_type)
async def process_product_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(type=message.text)
    await state.set_state(ProductForm.waiting_for_sizes)
    await message.answer(
        'Этап 5/7\nВведите размер:',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_sizes)
async def process_product_sizes(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(sizes=message.text)
    await state.set_state(ProductForm.waiting_for_price)
    await message.answer(
        'Этап 6/7\nВведите цену:',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.message(ProductForm.waiting_for_price)
async def process_product_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(price=message.text)
    await state.set_state(ProductForm.waiting_for_images)
    await message.answer(
        'Этап 7/7\nЗагрузите фото товара (можно несколько, по одному):',
        reply_markup=get_fsm_cancel_skip_kb()
    )

@router.callback_query(F.data == 'admin_manage_products')
async def admin_manage_products(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    new_text = 'Выберите категорию:'
    new_markup = get_admin_categories_kb()
    await safe_edit_text(call.message, new_text, new_markup)
    await state.clear()
    await state.update_data(admin_manage=True)

@router.callback_query(F.data.startswith('admin_cat_'))
async def admin_choose_category(call: CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    if not data_state.get('admin_manage'):
        return
    category = call.data.replace('admin_cat_', '')
    await state.update_data(category=category)
    # Выбор страны только для "soft" и "bedroom"
    if category in ['soft', 'bedroom']:
        new_text = 'Выберите страну:'
        new_markup = get_admin_countries_kb(category)
        await safe_edit_text(call.message, new_text, new_markup)
    elif category in ['bed', 'tables', 'dressers', 'mattress', 'wardrobe']:
        # Для этих категорий сразу отображаем товары без выбора страны и типа
        await show_products_for_category(call, state, category, None)
    else:
        # Для остальных категорий сразу отображаем товары/типы без выбора страны
        await show_products_for_category(call, state, category, None)

@router.callback_query(F.data.startswith('admin_country_'))
async def admin_choose_country(call: CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    if not data_state.get('admin_manage'):
        return
    rest = call.data[len('admin_country_'):]
    cat_and_country = rest.split('_', 1)
    if len(cat_and_country) < 2:
        return
    category = cat_and_country[0]
    country = urllib.parse.unquote_plus(cat_and_country[1])
    if country == 'None':
        country = None
    await show_products_for_category(call, state, category, country)

async def show_products_for_category(call: CallbackQuery, state: FSMContext, category: str, country: str = None):
    # Для этих категорий не показываем выбор типа, сразу выводим товары
    skip_type_categories = ['tables', 'dressers', 'mattress', 'bed', 'wardrobe']
    if category in skip_type_categories:
        from database.crud import get_products_by_params
        products = await get_products_by_params(category if category != 'all' else None, country, None)
        types = []
        if products:
            try:
                await call.message.delete()
            except TelegramBadRequest:
                pass
            from aiogram.types import InputMediaPhoto, FSInputFile
            async with async_session() as session:
                sent_message_ids = []
                for p in products:
                    price = p.price
                    if price is not None:
                        if float(price).is_integer():
                            price_str = f"{int(price):,}".replace(",", " ")
                        else:
                            price_str = f"{price:,.2f}".replace(",", " ").rstrip('0').rstrip('.')
                    else:
                        price_str = "-"
                    text = f"Название: {p.name}\n"
                    text += f"Описание: {p.description or '-'}\n"
                    text += f"Страна: {p.country or '-'}\n"
                    text += f"Размеры: {p.sizes or '-'}\n"
                    text += f"Цена: {price_str} ₽\n"
                    text += f"Тип: {p.type or '-'}"
                    photos = await get_photos_by_product(session, p.id)
                    media = []
                    for i, photo in enumerate(photos):
                        file_path = os.path.join('media', photo.filename)
                        if os.path.exists(file_path):
                            media.append(InputMediaPhoto(media=FSInputFile(file_path), caption=None if i > 0 else None))
                    if media:
                        media[0].caption = text
                        media[0].parse_mode = 'HTML'
                        try:
                            msgs = await call.message.answer_media_group(media)
                            sent_message_ids.extend([m.message_id for m in msgs])
                            msg = await call.message.answer('Выберите действие:', reply_markup=get_product_manage_kb(p.id, category))
                            sent_message_ids.append(msg.message_id)
                        except TelegramBadRequest:
                            msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                            sent_message_ids.append(msg.message_id)
                    else:
                        msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                        sent_message_ids.append(msg.message_id)
                await state.update_data(admin_product_message_ids=sent_message_ids)
            return
        # Никаких товаров нет
        new_text = 'Товары не найдены.'
        new_markup = get_back_admin_kb()
        try:
            if call.message.text != new_text or call.message.reply_markup != new_markup:
                await call.message.edit_text(new_text, reply_markup=new_markup)
        except TelegramBadRequest as e:
            if 'message to edit not found' in str(e):
                await call.message.answer(new_text, reply_markup=new_markup)
            else:
                raise
        return
    # ...existing code...
    if category in ['kitchen', 'soft'] and (country is None or country == 'Российская'):
        new_text = f'Вы выбрали страну: {country}\nТеперь выберите тип:'
        new_markup = get_admin_types_kb(category, country)
        await safe_edit_text(call.message, new_text, new_markup)
        return
    from database.crud import get_products_by_params
    products = await get_products_by_params(category if category != 'all' else None, country, None)
    types = []
    for p in products:
        if p.type and p.type not in types:
            types.append(p.type)
    if types:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        kb = InlineKeyboardBuilder()
        emoji_map = {
            'прямая': '➡️',
            'угловая': '↩️',
        }
        for t in types:
            label = f"{emoji_map.get(t, '')} {t}".strip()
            # Ограничиваем длину country и type для callback_data
            country_token = urllib.parse.quote_plus(country) if country is not None else 'None'
            type_token = urllib.parse.quote_plus(t)
            # Сокращаем до 10 символов, чтобы не превысить лимит Telegram
            country_token = country_token[:10]
            type_token = type_token[:10]
            callback_data = f'admin_type_{category[:10]}_{country_token}_{type_token}'
            if len(callback_data.encode('utf-8')) <= 64:
                kb.button(text=label, callback_data=callback_data)
            else:
                # Если превышает лимит, не добавляем кнопку
                continue
        kb.adjust(1)
        new_markup = kb.as_markup()
        new_text = f'Вы выбрали страну: {country}\nТеперь выберите тип:'
        await safe_edit_text(call.message, new_text, new_markup)
        return
    # Если типов нет — показываем товары (или сообщение о том, что их нет)
    if products:
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        from aiogram.types import InputMediaPhoto, FSInputFile
        async with async_session() as session:
            sent_message_ids = []
            for p in products:
                price = p.price
                if price is not None:
                    if float(price).is_integer():
                        price_str = f"{int(price):,}".replace(",", " ")
                    else:
                        price_str = f"{price:,.2f}".replace(",", " ").rstrip('0').rstrip('.')
                else:
                    price_str = "-"
                text = f"Название: {p.name}\n"
                text += f"Описание: {p.description or '-'}\n"
                text += f"Страна: {p.country or '-'}\n"
                text += f"Размеры: {p.sizes or '-'}\n"
                text += f"Цена: {price_str} ₽\n"
                text += f"Тип: {p.type or '-'}"
                photos = await get_photos_by_product(session, p.id)
                media = []
                for i, photo in enumerate(photos):
                    file_path = os.path.join('media', photo.filename)
                    if os.path.exists(file_path):
                        media.append(InputMediaPhoto(media=FSInputFile(file_path), caption=None if i > 0 else None))
                if media:
                    media[0].caption = text
                    media[0].parse_mode = 'HTML'
                    try:
                        msgs = await call.message.answer_media_group(media)
                        sent_message_ids.extend([m.message_id for m in msgs])
                        msg = await call.message.answer('Выберите действие:', reply_markup=get_product_manage_kb(p.id, category))
                        sent_message_ids.append(msg.message_id)
                    except TelegramBadRequest:
                        msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                        sent_message_ids.append(msg.message_id)
                else:
                    msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                    sent_message_ids.append(msg.message_id)
            await state.update_data(admin_product_message_ids=sent_message_ids)
        return
    # Никаких типов и товаров нет
    new_text = 'Товары не найдены.'
    new_markup = get_back_admin_kb()
    try:
        if call.message.text != new_text or call.message.reply_markup != new_markup:
            await call.message.edit_text(new_text, reply_markup=new_markup)
    except TelegramBadRequest as e:
        if 'message to edit not found' in str(e):
            await call.message.answer(new_text, reply_markup=new_markup)
        else:
            raise
    return

@router.callback_query(F.data == 'admin_back_type')
async def admin_back_type(call: CallbackQuery, state: FSMContext):
    # Возврат с уровня карточки товара на выбор типа
    data = await state.get_data()
    # удалить отображённые карточки, если были
    message_ids = data.get('admin_product_message_ids', [])
    for msg_id in message_ids:
        try:
            await call.bot.delete_message(call.message.chat.id, msg_id)
        except Exception:
            pass
    await state.update_data(admin_product_message_ids=[])

    category = data.get('category')
    country = data.get('country')
    new_text = f'Вы выбрали страну: {country}'
    new_markup = get_admin_types_kb(category, country)
    try:
        if call.message.text != new_text or call.message.reply_markup != new_markup:
            await call.message.edit_text(new_text, reply_markup=new_markup)
    except TelegramBadRequest:
        await call.message.answer(new_text, reply_markup=new_markup)

@router.callback_query(F.data == 'admin_back_country')
async def admin_back_country(call: CallbackQuery, state: FSMContext):
    # Возврат с уровня типов на выбор страны
    data = await state.get_data()
    # удалить отображённые карточки, если были
    message_ids = data.get('admin_product_message_ids', [])
    for msg_id in message_ids:
        try:
            await call.bot.delete_message(call.message.chat.id, msg_id)
        except Exception:
            pass
    await state.update_data(admin_product_message_ids=[])

    category = data.get('category')
    new_text = 'Выберите страну:'
    new_markup = get_admin_countries_kb(category)
    try:
        if call.message.text != new_text or call.message.reply_markup != new_markup:
            await call.message.edit_text(new_text, reply_markup=new_markup)
    except TelegramBadRequest:
        await call.message.answer(new_text, reply_markup=new_markup)

@router.callback_query(F.data == 'admin_back_category')
async def admin_back_category(call: CallbackQuery, state: FSMContext):
    # Возврат с уровня выбора страны/товаров на выбор категории
    data = await state.get_data()
    # удалить отображённые карточки, если были
    message_ids = data.get('admin_product_message_ids', [])
    for msg_id in message_ids:
        try:
            await call.bot.delete_message(call.message.chat.id, msg_id)
        except Exception:
            pass
    await state.update_data(admin_product_message_ids=[])

    # Категории, для которых всегда возвращаем на выбор категорий
    always_to_categories = ['tables', 'dressers', 'mattress', 'bed', 'wardrobe']
    category = data.get('category')
    if data.get('admin_manage') and category in always_to_categories:
        new_text = 'Выберите категорию:'
        new_markup = get_admin_categories_kb()
        try:
            if call.message.text != new_text or call.message.reply_markup != new_markup:
                await call.message.edit_text(new_text, reply_markup=new_markup)
        except TelegramBadRequest as e:
            if 'message to edit not found' in str(e):
                await call.message.answer(new_text, reply_markup=new_markup)
            else:
                raise
        await state.update_data(category=None)
        return

    # Если мы в режиме управления товарами — показать админ-категории
    if data.get('admin_manage'):
        new_text = 'Выберите категорию:'
        new_markup = get_admin_categories_kb()
        try:
            if call.message.text != new_text or call.message.reply_markup != new_markup:
                await call.message.edit_text(new_text, reply_markup=new_markup)
        except TelegramBadRequest as e:
            if 'message to edit not found' in str(e):
                await call.message.answer(new_text, reply_markup=new_markup)
            else:
                raise
        await state.update_data(category=None)
        return

    # Иначе — мы в процессе добавления товара (FSM) -> вернуться на выбор категории
    await state.update_data(category=None)
    try:
        # Пытемся отредактировать текущее сообщение
        new_text = 'Выберите категорию:'
        new_markup = get_categories_kb()
        if call.message and (call.message.text != new_text or call.message.reply_markup != new_markup):
            await call.message.edit_text(new_text, reply_markup=new_markup)
        else:
            await call.message.answer(new_text, reply_markup=new_markup)
    except TelegramBadRequest:
        await call.message.answer('Выберите категорию:', reply_markup=get_categories_kb())
    await state.set_state(ProductForm.waiting_for_category)

@router.callback_query(F.data.startswith('admin_type_'))
async def admin_manage_choose_type(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get('admin_manage'):
        return  # Не в режиме управления товарами
    try:
        await call.message.delete()
    except Exception:
        pass
    # Парсим параметры из callback_data: admin_type_{category}_{country}_{type}
    parts = call.data.split('_', 4)
    if len(parts) < 5:
        await call.answer('Ошибка выбора типа')
        return
    _, _, category, country, type_name = parts
    import urllib.parse
    country = urllib.parse.unquote_plus(country)
    type_name = urllib.parse.unquote_plus(type_name)
    from database.crud import get_products_by_params
    from aiogram.types import InputMediaPhoto, FSInputFile
    async with async_session() as session:
        products = await get_products_by_params(category, country, type_name)
        if not products:
            await call.message.answer('Товары не найдены.', reply_markup=get_back_admin_kb())
            return
        sent_message_ids = []
        for p in products:
            price = p.price
            if price is not None:
                if float(price).is_integer():
                    price_str = f"{int(price):,}".replace(",", " ")
                else:
                    price_str = f"{price:,.2f}".replace(",", " ").rstrip('0').rstrip('.')
            else:
                price_str = "-"
            text = f"Название: {p.name}\n"
            text += f"Описание: {p.description or '-'}\n"
            text += f"Страна: {p.country or '-'}\n"
            text += f"Размеры: {p.sizes or '-'}\n"
            text += f"Цена: {price_str} ₽\n"
            text += f"Тип: {p.type or '-'}"
            photos = await get_photos_by_product(session, p.id)
            media = []
            for i, photo in enumerate(photos):
                file_path = os.path.join('media', photo.filename)
                if os.path.exists(file_path):
                    media.append(InputMediaPhoto(media=FSInputFile(file_path), caption=None if i > 0 else None))
            if media:
                media[0].caption = text
                media[0].parse_mode = 'HTML'
                try:
                    msgs = await call.message.answer_media_group(media)
                    sent_message_ids.extend([m.message_id for m in msgs])
                    msg = await call.message.answer('Выберите действие:', reply_markup=get_product_manage_kb(p.id, category))
                    sent_message_ids.append(msg.message_id)
                except Exception:
                    msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                    sent_message_ids.append(msg.message_id)
            else:
                msg = await call.message.answer(text, reply_markup=get_product_manage_kb(p.id, category), parse_mode='HTML')
                sent_message_ids.append(msg.message_id)
        await state.update_data(admin_product_message_ids=sent_message_ids)
    await call.answer()

@router.callback_query(F.data == 'to_user_panel')
async def to_user_panel_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Вы перешли в пользовательскую панель.', reply_markup=main_menu_kb)

@router.callback_query(F.data == 'fsm_cancel')
async def fsm_cancel_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(F.data == 'fsm_skip')
async def fsm_skip_handler(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    # Переход к следующему этапу FSM
    next_state = {
        'ProductForm:waiting_for_name': ProductForm.waiting_for_category,
        'ProductForm:waiting_for_category': ProductForm.waiting_for_subcategory,
        'ProductForm:waiting_for_subcategory': ProductForm.waiting_for_country,
        'ProductForm:waiting_for_country': ProductForm.waiting_for_type,
        'ProductForm:waiting_for_type': ProductForm.waiting_for_sizes,
        'ProductForm:waiting_for_sizes': ProductForm.waiting_for_price,
        'ProductForm:waiting_for_price': ProductForm.waiting_for_images,
    }.get(current_state, None)
    if next_state:
        await state.set_state(next_state)
        step_texts = {
            ProductForm.waiting_for_category: 'Этап 2/7\nВыберите категорию товара:',
            ProductForm.waiting_for_subcategory: 'Этап 2.1/7\nВведите подкатегорию товара (или пропустите):',
            ProductForm.waiting_for_country: 'Этап 3/7\nВведите страну производства:',
            ProductForm.waiting_for_type: 'Этап 4/7\nВведите тип (прямая, угловая и т.п.):',
            ProductForm.waiting_for_sizes: 'Этап 5/7\nВведите размер:',
            ProductForm.waiting_for_price: 'Этап 6/7\nВведите цену:',
            ProductForm.waiting_for_images: 'Этап 7/7\nЗагрузите фото товара (можно несколько, по одному):',
        }
        await call.message.edit_text(step_texts[next_state], reply_markup=get_fsm_cancel_skip_kb())
    else:
        await call.message.edit_text('Добавление товара завершено или произошла ошибка.', reply_markup=get_admin_main_kb())
        await state.clear()

@router.message(ProductForm.waiting_for_images)
async def process_product_images(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    images = data.get('images', [])
    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        filename = f"product_{message.from_user.id}_{uuid.uuid4().hex}.jpg"
        file_on_disk = os.path.join('media', filename)
        await message.bot.download_file(file_path, file_on_disk)
        images.append(filename)
        await state.update_data(images=images)
        await message.answer('Фото добавлено. Можете отправить ещё или нажмите ⏭️ Пропустить для завершения.', reply_markup=get_fsm_cancel_skip_kb())
        return
    # --- Сохранение товара ---
    # Собираем все данные
    name = data.get('name')
    category = data.get('category')
    subcategory = data.get('subcategory')
    country = data.get('country')
    type_ = data.get('type')
    sizes = data.get('sizes')
    price = data.get('price')
    images_str = ';'.join(images) if images else None
    # Приведение типов
    try:
        category_enum = ProductCategory(category) if category else None
    except Exception:
        category_enum = None
    try:
        price_val = float(price) if price else None
    except Exception:
        price_val = None
    # Сохраняем в БД
    async with async_session() as session:
        try:
            product = await add_product(
                session,
                name=name,
                category=category_enum,
                subcategory=subcategory,
                country=country,
                type=type_,
                sizes=sizes,
                price=price_val,
                images=images_str
            )
            await message.answer(f'Товар успешно добавлен! ✅\nID: {product.id}', reply_markup=get_admin_main_kb())
        except Exception as e:
            await message.answer(f'Ошибка при добавлении товара: {e}', reply_markup=get_admin_main_kb())
    await state.clear()

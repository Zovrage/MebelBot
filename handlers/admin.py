from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.models import ProductCategory
from database.crud import update_product, get_products
from keyboards.admin import admin_main_kb, get_add_step_kb, get_country_kb, get_type_kb, get_edit_fields_kb, get_category_add_kb, get_leads_kb, get_lead_status_kb, get_category_kb, get_product_manage_kb, get_back_to_admin_kb
from database.db import async_session
from states.admin import EditProductForm, ProductForm, AdminProductFilter
from config import ADMIN_IDS
from handlers.user import get_country_display, get_type_display
import os
from aiogram.types import FSInputFile
from database.crud import get_photos_by_product


# Проверка, является ли пользователь админом
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

router = Router()

# Вход в админ-панель
@router.callback_query(F.data == 'admin_panel')
async def admin_panel_entry(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.message.answer('Доступ запрещён.')
        await callback.answer()
        return
    # Удаляем прошлое сообщение (меню пользователя)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('⚙️ Админская панель', reply_markup=admin_main_kb)
    await callback.answer()

# Редактирование товара: выбор поля
@router.callback_query(F.data.startswith("edit_"))
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_", 1)[1])
    await state.update_data(product_id=product_id)
    fields = [
        ("name", "Название"),
        ("category", "Категория"),
        ("subcategory", "Подкатегория"),
        ("country", "Страна"),
        ("type", "Тип"),
        ("sizes", "Размер"),
        ("price", "Цена"),
        ("description", "Описание")
    ]
    kb = get_edit_fields_kb(fields)
    await callback.message.answer("Выберите поле для редактирования:", reply_markup=kb)
    await state.set_state(EditProductForm.waiting_for_field)
    await callback.answer()

@router.callback_query(EditProductForm.waiting_for_field, F.data.startswith("editfield_"))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_", 1)[1]
    await state.update_data(field=field)
    await callback.message.answer(f"Введите новое значение для поля: {field}")
    await state.set_state(EditProductForm.waiting_for_value)
    await callback.answer()

@router.message(EditProductForm.waiting_for_value)
async def edit_product_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]
    value = message.text
    # Преобразование типов для некоторых полей
    if field == "price":
        try:
            value = float(value.replace(",", "."))
        except ValueError:
            await message.answer("Введите корректную цену!")
            return
    if field == "category":
        value = value if value in ProductCategory.__members__ else None
        if not value:
            await message.answer("Некорректная категория!")
            return

    async with async_session() as session:
        await update_product(session, product_id, **{field: value})
    await state.clear()
    await message.answer("Товар обновлён.", reply_markup=admin_main_kb)

# --- Добавление товара ---
@router.callback_query(F.data == 'add_product')
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.clear()
    await state.set_state(ProductForm.waiting_for_name)
    await callback.message.answer(
        'Введите название товара:',
        reply_markup=get_add_step_kb()
    )
    await callback.answer()

@router.message(ProductForm.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text:
        await state.update_data(name=message.text)
    await state.set_state(ProductForm.waiting_for_category)
    await message.answer('Выберите категорию товара:', reply_markup=get_category_add_kb())

@router.callback_query(ProductForm.waiting_for_category, F.data.startswith('category_'))
async def add_product_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split('_', 1)[1]
    await state.update_data(category=category)
    await state.set_state(ProductForm.waiting_for_subcategory)
    await callback.message.answer('Введите подкатегорию (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    await callback.answer()

@router.message(ProductForm.waiting_for_subcategory)
async def add_product_subcategory(message: Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    data = await state.get_data()
    category = data.get('category')
    if category in ['soft', 'bedroom']:
        await state.set_state(ProductForm.waiting_for_country)
        await message.answer('Выберите страну производства:', reply_markup=get_country_kb())
    elif category == 'kitchen':
        await state.set_state(ProductForm.waiting_for_type)
        await message.answer('Выберите тип товара:', reply_markup=get_type_kb())
    else:
        await state.set_state(ProductForm.waiting_for_sizes)
        await message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.callback_query(ProductForm.waiting_for_country, F.data.startswith('country_'))
async def add_product_country_callback(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split('_', 1)[1]
    if code == 'skip_country':
        await state.update_data(country=None)
    else:
        await state.update_data(country=code)
    data = await state.get_data()
    category = data.get('category')
    country = code
    if category in ['soft', 'bedroom']:
        if country == 'russia':
            await state.set_state(ProductForm.waiting_for_type)
            await callback.message.edit_text('Выберите тип товара:', reply_markup=get_type_kb())
        else:
            await state.set_state(ProductForm.waiting_for_sizes)
            await callback.message.edit_text('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif category == 'kitchen':
        await state.set_state(ProductForm.waiting_for_type)
        await callback.message.edit_text('Выберите тип товара:', reply_markup=get_type_kb())
    else:
        await state.set_state(ProductForm.waiting_for_sizes)
        await callback.message.edit_text('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    await callback.answer()

@router.message(ProductForm.waiting_for_country)
async def add_product_country_text(message: Message, state: FSMContext):
    await state.update_data(country=message.text)
    data = await state.get_data()
    category = data.get('category')
    country = message.text.lower()
    if category in ['soft', 'bedroom']:
        if country == 'russia' or country == 'россия':
            await state.set_state(ProductForm.waiting_for_type)
            await message.answer('Выберите тип товара:', reply_markup=get_type_kb())
        else:
            await state.set_state(ProductForm.waiting_for_sizes)
            await message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif category == 'kitchen':
        await state.set_state(ProductForm.waiting_for_type)
        await message.answer('Выберите тип товара:', reply_markup=get_type_kb())
    else:
        await state.set_state(ProductForm.waiting_for_sizes)
        await message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.callback_query(ProductForm.waiting_for_type, F.data.startswith('type_'))
async def add_product_type_callback(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split('_', 1)[1]
    if code == 'skip_type':
        await state.update_data(type=None)
    else:
        await state.update_data(type=code)
    data = await state.get_data()
    category = data.get('category')
    # Исправлено: после выбора типа для soft переходим к размеру, а не к стране
    await state.set_state(ProductForm.waiting_for_sizes)
    await callback.message.edit_text('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    await callback.answer()

@router.message(ProductForm.waiting_for_type)
async def add_product_type_text(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    data = await state.get_data()
    category = data.get('category')
    if category == 'soft':
        await state.set_state(ProductForm.waiting_for_country)
        await message.answer('Выберите страну производства:', reply_markup=get_country_kb())
    elif category == 'kitchen':
        await state.set_state(ProductForm.waiting_for_sizes)
        await message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    else:
        await state.set_state(ProductForm.waiting_for_sizes)
        await message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.message(ProductForm.waiting_for_sizes)
async def add_product_sizes(message: Message, state: FSMContext):
    await state.update_data(sizes=message.text)
    await state.set_state(ProductForm.waiting_for_price)
    await message.answer('Введите цену (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.message(ProductForm.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
    except Exception:
        price = None
    await state.update_data(price=price)
    await state.set_state(ProductForm.waiting_for_description)
    await message.answer('Введите описание (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.message(ProductForm.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductForm.waiting_for_images)
    await message.answer('Отправьте фото товара (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())

@router.message(ProductForm.waiting_for_images, F.photo)
async def add_product_images(message: Message, state: FSMContext):
    data = await state.get_data()
    product_data = data.copy()
    # Если товара ещё нет в БД, создаём его без фото
    if not data.get('product_id'):
        from database.db import async_session
        from database.crud import add_product
        async with async_session() as session:
            product = await add_product(session, **product_data)
            await state.update_data(product_id=product.id)
    product_id = (await state.get_data()).get('product_id')
    # Сохраняем фото в media
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path
    # Генерируем уникальное имя файла
    filename = f"{product_id}_{photo.file_id}.jpg"
    dest_path = os.path.join('media', filename)
    await message.bot.download_file(file_path, dest_path)
    # Сохраняем запись о фото в БД
    from database.db import async_session
    async with async_session() as session:
        await add_photo(session, product_id=product_id, filename=filename, original_file_id=photo.file_id)
    # Считаем количество фото для этого товара
    from database.crud import get_photos_by_product
    async with async_session() as session:
        photos = await get_photos_by_product(session, product_id)
    if len(photos) >= 5:
        await finish_add_product(message, state)
        return
    await message.answer(f'Фото добавлено ({len(photos)}/5). Можете отправить ещё или нажмите ⏭️ Пропустить, если достаточно.', reply_markup=get_add_step_kb())

@router.message(ProductForm.waiting_for_images)
async def add_product_images_text(message: Message, state: FSMContext):
    await finish_add_product(message, state)

@router.callback_query(ProductForm.waiting_for_images, F.data == 'skip')
async def skip_product_images(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_data = data.copy()
    if not data.get('product_id'):
        from database.db import async_session
        from database.crud import add_product
        async with async_session() as session:
            product = await add_product(session, **product_data)
    await state.clear()
    await callback.message.answer('Товар добавлен без фото.', reply_markup=admin_main_kb)
    await callback.answer()

async def finish_add_product(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Товар успешно добавлен!', reply_markup=admin_main_kb)

# Обработка возврата на главное меню
@router.callback_query(F.data == 'back_main')
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from keyboards.user import main_menu_kb
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('Главное меню', reply_markup=main_menu_kb)
    await callback.answer()

@router.callback_query(F.data == 'leads')
async def view_leads(callback: CallbackQuery, state: FSMContext):
    from database.db import async_session
    from database.crud import get_leads
    from keyboards.admin import get_lead_status_kb
    try:
        await callback.message.delete()
    except Exception:
        pass
    async with async_session() as session:
        leads = await get_leads(session)
    if not leads:
        await callback.message.answer('Заявок нет.', reply_markup=get_lead_status_kb('none'))
        await callback.answer()
        return
    lead_message_ids = []
    for lead in leads:
        product_name = getattr(lead.product, 'name', '-') if lead.product else '-'
        text = (
            f"<b>{lead.name}</b>\n"
            f"Телефон: <code>{lead.phone}</code>\n"
            f"Товар: {product_name}\n"
            f"Статус: {lead.status.value if hasattr(lead.status, 'value') else lead.status}\n"
            f"Комментарий: {lead.comment or '-'}"
        )
        msg = await callback.message.answer(text, parse_mode='HTML', reply_markup=get_lead_status_kb(lead.id))
        lead_message_ids.append(msg.message_id)
    # Сохраняем id сообщений с заявками в FSM
    await state.update_data(admin_lead_message_ids=lead_message_ids)
    await callback.answer()

@router.callback_query(F.data.regexp(r'^lead_status_(new|in_progress|closed)_\d+$'))
async def change_lead_status(callback: CallbackQuery):
    from database.db import async_session
    from database.crud import update_lead_status, get_leads
    from database.models import LeadStatus
    from keyboards.admin import get_lead_status_kb
    import re
    match = re.match(r'^lead_status_(new|in_progress|closed)_(\d+)$', callback.data)
    if not match:
        await callback.answer('Ошибка данных')
        return
    status_str, lead_id = match.group(1), int(match.group(2))
    # Преобразуем строку в Enum
    status_enum = LeadStatus[status_str]
    async with async_session() as session:
        await update_lead_status(session, lead_id, status_enum)
        # Получаем обновлённую заявку
        leads = await get_leads(session)
        lead = next((l for l in leads if l.id == lead_id), None)
    if not lead:
        await callback.answer('Заявка не найдена')
        return
    product_name = getattr(lead.product, 'name', '-') if lead.product else '-'
    text = (
        f"<b>{lead.name}</b>\n"
        f"Телефон: <code>{lead.phone}</code>\n"
        f"Товар: {product_name}\n"
        f"Статус: {lead.status.value if hasattr(lead.status, 'value') else lead.status}\n"
        f"Комментарий: {lead.comment or '-'}"
    )
    try:
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=get_lead_status_kb(lead.id))
    except Exception:
        pass
    await callback.answer('Статус обновлён')

@router.callback_query(F.data == 'back_to_admin')
async def back_to_admin_panel(callback: CallbackQuery, state: FSMContext):
    from keyboards.admin import admin_main_kb
    # Удаляем все сообщения с заявками
    data = await state.get_data()
    lead_message_ids = data.get('admin_lead_message_ids', [])
    for msg_id in lead_message_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception:
            pass
    await state.update_data(admin_lead_message_ids=[])
    # Удаляем все сообщения с карточками товаров
    product_message_ids = data.get('admin_product_message_ids', [])
    for msg_id in product_message_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception:
            pass
    await state.update_data(admin_product_message_ids=[])
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('⚙️ Админская панель', reply_markup=admin_main_kb)
    await callback.answer()

@router.callback_query(F.data.regexp(r'^delete_lead_\d+$'))
async def delete_lead_handler(callback: CallbackQuery):
    from database.db import async_session
    from database.crud import delete_lead
    import re
    match = re.match(r'^delete_lead_(\d+)$', callback.data)
    if not match:
        await callback.answer('Ошибка данных')
        return
    lead_id = int(match.group(1))
    async with async_session() as session:
        await delete_lead(session, lead_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer('Заявка удалена')

# --- Управление товарами: пошаговая фильтрация ---
@router.callback_query(F.data == 'manage_products')
async def manage_products(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.clear()
    await state.set_state(AdminProductFilter.waiting_for_category)
    kb = get_category_kb()
    # Добавляем кнопку "Назад"
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")])
    await callback.message.answer('Выберите категорию для управления товарами:', reply_markup=kb)
    await callback.answer()

@router.callback_query(AdminProductFilter.waiting_for_category, F.data.startswith('category_'))
async def admin_select_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split('_', 1)[1]
    await state.update_data(category=category)
    await state.set_state(AdminProductFilter.waiting_for_country)
    kb = get_country_kb()
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_category")])
    await callback.message.edit_text('Выберите страну:', reply_markup=kb)
    await callback.answer()

@router.callback_query(AdminProductFilter.waiting_for_country, F.data.startswith('country_'))
async def admin_select_country(callback: CallbackQuery, state: FSMContext):
    country = callback.data.split('_', 1)[1]
    await state.update_data(country=country)
    await state.set_state(AdminProductFilter.waiting_for_type)
    kb = get_type_kb()
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_country")])
    await callback.message.edit_text('Выберите тип:', reply_markup=kb)
    await callback.answer()

@router.callback_query(AdminProductFilter.waiting_for_type, F.data.startswith('type_'))
async def admin_select_type(callback: CallbackQuery, state: FSMContext):
    type_ = callback.data.split('_', 1)[1]
    data = await state.get_data()
    category = data.get('category')
    country = data.get('country')
    await state.update_data(type=type_)
    await admin_show_products(callback, category=category, country=country, type_=type_, state=state)

# --- Кнопки "Назад" для фильтрации ---
@router.callback_query(AdminProductFilter.waiting_for_country, F.data == 'back_to_admin_category')
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminProductFilter.waiting_for_category)
    kb = get_category_kb()
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")])
    await callback.message.edit_text('Выберите категорию для управления товарами:', reply_markup=kb)
    await callback.answer()

@router.callback_query(AdminProductFilter.waiting_for_type, F.data == 'back_to_admin_country')
async def back_to_country(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data.get('category')
    await state.set_state(AdminProductFilter.waiting_for_country)
    kb = get_country_kb()
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin_category")])
    await callback.message.edit_text('Выберите страну:', reply_markup=kb)
    await callback.answer()

async def admin_show_products(callback, category=None, country=None, type_=None, state: FSMContext = None):
    try:
        await callback.message.delete()
    except Exception:
        pass
    # Удаляем предыдущие сообщения с товарами (если есть)
    if state is not None:
        data = await state.get_data()
        prev_product_msgs = data.get('admin_product_message_ids', [])
        for msg_id in prev_product_msgs:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except Exception:
                pass
        await state.update_data(admin_product_message_ids=[])
    async with async_session() as session:
        products = await get_products(session, category=category, country=country, type_=type_)
        if not products:
            await callback.message.answer('Товаров нет.', reply_markup=get_back_to_admin_kb())
            await callback.answer()
            return
        product_message_ids = []
        for product in products:
            photos = await get_photos_by_product(session, product.id)
            media = []
            for i, photo in enumerate(photos):
                file_path = os.path.join('media', photo.filename)
                if os.path.exists(file_path):
                    media.append(FSInputFile(file_path))
            price = product.price
            if price is None or price == 0:
                price_str = '-'
            else:
                price_str = f"{int(price) if float(price).is_integer() else price} ₽"
            caption = (
                f"<b>Название:</b> {product.name}\n"
                f"<b>Описание:</b> {product.description or '-'}\n"
                f"<b>Страна:</b> {get_country_display(product.country)}\n"
                f"<b>Тип:</b> {get_type_display(getattr(product, 'type', None))}\n"
                f"<b>Размеры:</b> {getattr(product, 'sizes', '-') or '-'}\n"
                f"<b>Цена:</b> {price_str}"
            )
            if media:
                if len(media) == 1:
                    msg = await callback.message.answer_photo(media[0], caption=caption, parse_mode='HTML', reply_markup=get_product_manage_kb(product.id))
                    product_message_ids.append(msg.message_id)
                else:
                    from aiogram.types import InputMediaPhoto
                    media_group = [InputMediaPhoto(media=FSInputFile(os.path.join('media', p.filename)), caption=caption if i == 0 else None, parse_mode='HTML' if i == 0 else None) for i, p in enumerate(photos)]
                    msgs = await callback.message.answer_media_group(media_group)
                    for m in msgs:
                        product_message_ids.append(m.message_id)
                    msg2 = await callback.message.answer('Выберите действие:', reply_markup=get_product_manage_kb(product.id))
                    product_message_ids.append(msg2.message_id)
            else:
                msg = await callback.message.answer(
                    caption,
                    reply_markup=get_product_manage_kb(product.id),
                    parse_mode='HTML'
                )
                product_message_ids.append(msg.message_id)
        await state.update_data(admin_product_message_ids=product_message_ids)
    await callback.answer()

@router.callback_query(F.data == "back_to_product_manage")
async def back_to_product_manage(callback: CallbackQuery, state: FSMContext):
    # Получаем фильтры из состояния
    data = await state.get_data()
    category = data.get('category')
    country = data.get('country')
    type_ = data.get('type')
    await admin_show_products(callback, category=category, country=country, type_=type_, state=state)
    await callback.answer()

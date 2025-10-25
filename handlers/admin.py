from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.models import ProductCategory
from database.crud import update_product
from keyboards.admin import admin_main_kb, get_add_step_kb, get_country_kb, get_type_kb, get_edit_fields_kb
from database.db import async_session
from states.admin import EditProductForm, ProductForm


router = Router()

# Вход в админ-панель
@router.callback_query(F.data == 'admin_panel')
async def admin_panel_entry(callback: CallbackQuery, state: FSMContext):
    # Удаляем прошлое сообщение (меню пользователя)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('Вы вошли в админ-панели.', reply_markup=admin_main_kb)
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
    from keyboards.admin import get_category_kb
    await message.answer('Выберите категорию товара:', reply_markup=get_category_kb())

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
    if category == 'soft':
        await state.set_state(ProductForm.waiting_for_country)
        await callback.message.edit_text('Выберите страну производства:', reply_markup=get_country_kb())
    elif category == 'kitchen':
        await state.set_state(ProductForm.waiting_for_sizes)
        await callback.message.edit_text('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    else:
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
    # Для простоты: сохраняем file_id первой фотографии
    await state.update_data(images=message.photo[-1].file_id)
    await finish_add_product(message, state)

@router.message(ProductForm.waiting_for_images)
async def add_product_images_text(message: Message, state: FSMContext):
    # Если не фото, а текст — пропускаем
    await finish_add_product(message, state)

@router.callback_query(F.data == 'add_skip')
async def add_product_skip(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    category = data.get('category')
    # Пропуск — просто пустое значение
    if current_state == ProductForm.waiting_for_subcategory.state:
        await state.update_data(subcategory=None)
        # Логика следующего шага как в add_product_subcategory
        if category == 'soft':
            await state.set_state(ProductForm.waiting_for_country)
            await callback.message.answer('Выберите страну производства:', reply_markup=get_country_kb())
        elif category == 'bedroom':
            await state.set_state(ProductForm.waiting_for_country)
            await callback.message.answer('Выберите страну производства:', reply_markup=get_country_kb())
        elif category == 'kitchen':
            await state.set_state(ProductForm.waiting_for_type)
            await callback.message.answer('Выберите тип товара:', reply_markup=get_type_kb())
        else:
            await state.set_state(ProductForm.waiting_for_sizes)
            await callback.message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_country.state:
        await state.update_data(country=None)
        # После страны всегда размер
        await state.set_state(ProductForm.waiting_for_sizes)
        await callback.message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_type.state:
        await state.update_data(type=None)
        # Логика следующего шага как in add_product_type_callback
        if category == 'soft':
            await state.set_state(ProductForm.waiting_for_country)
            await callback.message.answer('Выберите страну производства:', reply_markup=get_country_kb())
        elif category == 'kitchen':
            await state.set_state(ProductForm.waiting_for_sizes)
            await callback.message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
        else:
            await state.set_state(ProductForm.waiting_for_sizes)
            await callback.message.answer('Введите размер (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_sizes.state:
        await state.update_data(sizes=None)
        await state.set_state(ProductForm.waiting_for_price)
        await callback.message.answer('Введите цену (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_price.state:
        await state.update_data(price=None)
        await state.set_state(ProductForm.waiting_for_description)
        await callback.message.answer('Введите описание (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_description.state:
        await state.update_data(description=None)
        await state.set_state(ProductForm.waiting_for_images)
        await callback.message.answer('Отправьте фото товара (или ⏭️ Пропустить):', reply_markup=get_add_step_kb())
    elif current_state == ProductForm.waiting_for_images.state:
        await state.update_data(images=None)
        # Завершить добавление
        await finish_add_product(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == 'add_cancel')
async def add_product_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Добавление товара отменено.', reply_markup=admin_main_kb)
    await callback.answer()

@router.callback_query(ProductForm.waiting_for_country, F.data == 'country_cancel_country')
async def cancel_country(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Добавление товара отменено.', reply_markup=admin_main_kb)
    await callback.answer()

@router.callback_query(ProductForm.waiting_for_type, F.data == 'type_cancel_type')
async def cancel_type(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Добавление товара отменено.', reply_markup=admin_main_kb)
    await callback.answer()

async def finish_add_product(message: Message, state: FSMContext):
    data = await state.get_data()
    from database.db import async_session
    from database.crud import add_product
    # Преобразование категории
    if 'category' in data and data['category']:
        from database.models import ProductCategory
        data['category'] = ProductCategory[data['category']]
    async with async_session() as session:
        await add_product(session, **data)
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

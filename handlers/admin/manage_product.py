import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputFile
from aiogram.fsm.context import FSMContext

from keyboards.admin.manage_product import get_edit_fields_kb, get_product_manage_kb
from keyboards.admin.add_product import get_category_kb, get_country_kb, get_type_kb
from states.admin import EditProductForm, ManageProductFilter
from database.db import async_session
from database.crud import get_all_products, update_product, update_product_photo, delete_product, get_products
from database.models import CATEGORY_DISPLAY



router = Router()

# Вывод списка товаров для управления
@router.callback_query(F.data == "show_products_manage")
async def show_products_manage(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        products = await get_all_products(session)
    if not products:
        await callback.message.answer("Нет товаров для управления.")
        await callback.answer()
        return
    for product in products:
        category_display = CATEGORY_DISPLAY.get(product.category, str(product.category))
        text = (
            f"Название: {product.name}\n"
            f"Категория: {category_display}\n"
            f"Страна: {product.country or '-'}\n"
            f"Тип: {product.type or '-'}\n"
            f"Размеры: {product.sizes or '-'}\n"
            f"Цена: {int(product.price) if float(product.price).is_integer() else product.price} ₽\n"
            f"Описание: {product.description or '-'}"
        )
        kb = get_product_manage_kb(product.id)
        # Отправка фото(ок)
        if product.images:
            for img_path in product.images.split(';'):
                img_path = img_path.strip()
                if not img_path:
                    continue
                # Если это file_id Telegram (нет расширения и длина > 20)
                if len(img_path) > 20 and '.' not in img_path:
                    try:
                        await callback.message.answer_photo(photo=img_path)
                    except Exception:
                        await callback.message.answer("[Ошибка отправки фото по file_id]")
                # Если это локальный файл
                elif os.path.isfile(img_path):
                    try:
                        await callback.message.answer_photo(photo=InputFile(img_path))
                    except Exception:
                        await callback.message.answer(f"[Ошибка открытия файла: {img_path}]")
                else:
                    await callback.message.answer(f"[Фото не найдено: {img_path}]")
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

# Начало редактирования товара
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
        ("description", "Описание"),
        ("photo", "Фото")
    ]
    kb = get_edit_fields_kb(fields)
    await callback.message.answer("Выберите поле для редактирования:", reply_markup=kb)
    await state.set_state(EditProductForm.waiting_for_field)
    await callback.answer()

# Выбор поля для редактирования
@router.callback_query(EditProductForm.waiting_for_field, F.data.startswith("editfield_"))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_", 1)[1]
    await state.update_data(field=field)
    if field == "photo":
        await callback.message.answer("Отправьте новое фото для товара.")
        await state.set_state(EditProductForm.waiting_for_photo)
    else:
        await callback.message.answer(f"Введите новое значение для поля: {field}")
        await state.set_state(EditProductForm.waiting_for_value)
    await callback.answer()

# Обработка нового значения поля
@router.message(EditProductForm.waiting_for_value)
async def edit_product_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]
    value = message.text
    async with async_session() as session:
        await update_product(session, product_id, **{field: value})
    await message.answer(f"Поле '{field}' успешно обновлено!")
    await state.clear()

# Обработка нового фото
@router.message(EditProductForm.waiting_for_photo)
async def edit_product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото как изображение, а не как файл.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = f"media/product_{product_id}_{photo.file_id}.jpg"
    await message.bot.download_file(file.file_path, file_path)
    async with async_session() as session:
        await update_product_photo(session, product_id, file_path, photo.file_id)
    await message.answer("Фото товара успешно обновлено!")
    await state.clear()

# Удаление товара
@router.callback_query(F.data.startswith("delete_"))
async def delete_product_handler(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_", 1)[1])
    async with async_session() as session:
        await delete_product(session, product_id)
    await callback.message.answer("Товар удалён.")
    await callback.answer()

# Запуск фильтрации товаров
@router.callback_query(F.data == "filter_products")
async def filter_products_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите фильтр (например, категорию или страну):")
    await state.set_state(ManageProductFilter.waiting_for_filter)
    await callback.answer()

# Обработка фильтра
@router.message(ManageProductFilter.waiting_for_filter)
async def filter_products_value(message: Message, state: FSMContext):
    filter_value = message.text
    # Здесь можно реализовать фильтрацию по категории, стране и т.д.
    await message.answer(f"Фильтр применён: {filter_value}")
    await state.clear()

# Обработчик для кнопки "Управление товарами" из админ-панели
@router.callback_query(F.data == "manage_products")
async def manage_products_entry(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Выберите категорию:", reply_markup=get_category_kb())
    await state.clear()

# Обработчик кнопки "Назад" из категорий
@router.callback_query(F.data == "back_to_admin")
async def back_to_admin_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    from keyboards.admin.admin import admin_main_kb
    await callback.message.answer('⚙️ Админская панель', reply_markup=admin_main_kb)
    await callback.answer()

# Выбор категории
@router.callback_query(F.data.startswith("category_"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    category_code = callback.data.replace("category_", "")
    await state.update_data(manage_category=category_code)
    await callback.message.answer("Выберите страну:", reply_markup=get_country_kb())
    await callback.answer()

# Выбор страны
@router.callback_query(F.data.startswith("country_"))
async def choose_country(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    country_code = callback.data.replace("country_", "")
    await state.update_data(manage_country=country_code)
    await callback.message.answer("Выберите тип:", reply_markup=get_type_kb())
    await callback.answer()

# Выбор типа и вывод товаров
@router.callback_query(F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    type_code = callback.data.replace("type_", "")
    await state.update_data(manage_type=type_code)
    data = await state.get_data()
    category = data.get("manage_category")
    country = data.get("manage_country")
    type_ = data.get("manage_type")
    async with async_session() as session:
        products = await get_products(session, category=category, country=country, type_=type_)
    if not products:
        await callback.message.answer("Нет товаров по выбранным параметрам.")
        await callback.answer()
        return
    for product in products:
        category_display = CATEGORY_DISPLAY.get(product.category, str(product.category))
        text = (
            f"Название: {product.name}\n"
            f"Категория: {category_display}\n"
            f"Страна: {product.country or '-'}\n"
            f"Тип: {product.type or '-'}\n"
            f"Размеры: {product.sizes or '-'}\n"
            f"Цена: {int(product.price) if float(product.price).is_integer() else product.price} ₽\n"
            f"Описание: {product.description or '-'}"
        )
        kb = get_product_manage_kb(product.id)
        # Отправка фото(ок)
        if product.images:
            for img_path in product.images.split(';'):
                img_path = img_path.strip()
                if not img_path:
                    continue
                # Если это file_id Telegram (нет расширения и длина > 20)
                if len(img_path) > 20 and '.' not in img_path:
                    try:
                        await callback.message.answer_photo(photo=img_path)
                    except Exception:
                        await callback.message.answer("[Ошибка отправки фото по file_id]")
                # Если это локальный файл
                elif os.path.isfile(img_path):
                    try:
                        await callback.message.answer_photo(photo=InputFile.from_path(img_path))
                    except Exception:
                        await callback.message.answer(f"[Ошибка открытия файла: {img_path}]")
                else:
                    await callback.message.answer(f"[Фото не найдено: {img_path}]")
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

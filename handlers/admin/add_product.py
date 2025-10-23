from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.admin.add_product import get_skip_cancel_kb, get_confirm_add_kb, get_country_kb, get_type_kb, get_images_done_kb, get_category_kb
from keyboards.admin.admin import admin_main_kb
from database.crud import add_product
from database.db import async_session
from states.admin import ProductForm

router = Router()

# Добавление товара
@router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите название товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_name)
    await callback.answer()

# Обработка названия товара
@router.message(ProductForm.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Выберите категорию товара:", reply_markup=get_category_kb())
    await state.set_state(ProductForm.waiting_for_category)

# Callback для пропуска названия
@router.callback_query(ProductForm.waiting_for_name, F.data == "add_skip")
async def skip_name(callback: CallbackQuery, state: FSMContext):
    await state.update_data(name=None)
    await callback.message.answer("Выберите категорию товара:", reply_markup=get_category_kb())
    await state.set_state(ProductForm.waiting_for_category)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_name, F.data == "add_cancel")
async def cancel_add_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Callback для выбора категории
@router.callback_query(ProductForm.waiting_for_category, F.data.startswith("category_"))
async def add_product_category_callback(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("category_", "")
    await state.update_data(category=category)
    await callback.message.answer("Введите подкатегорию товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_subcategory)
    await callback.answer()

# Callback для пропуска категории
@router.callback_query(ProductForm.waiting_for_category, F.data == "add_skip")
async def skip_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=None)
    await callback.message.answer("Введите подкатегорию товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_subcategory)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_category, F.data == "add_cancel")
async def cancel_add_product_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Обработка подкатегории товара
@router.message(ProductForm.waiting_for_subcategory)
async def add_product_subcategory(message: Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    data = await state.get_data()
    category = data.get('category')
    # Страна только для мягкой и спальной мебели
    if category in ('soft', 'bedroom'):
        await message.answer("Выберите страну производства:", reply_markup=get_country_kb())
        await state.set_state(ProductForm.waiting_for_country)
    elif category in ('kitchen'):
        # Для кухни сразу к типу
        await message.answer("Выберите тип товара:", reply_markup=get_type_kb())
        await state.set_state(ProductForm.waiting_for_type)
    else:
        # Для остальных категорий сразу к размерам
        await message.answer("Введите размеры товара:", reply_markup=get_skip_cancel_kb())
        await state.set_state(ProductForm.waiting_for_sizes)

# Callback для пропуска подкатегории
@router.callback_query(ProductForm.waiting_for_subcategory, F.data == "add_skip")
async def skip_subcategory(callback: CallbackQuery, state: FSMContext):
    await state.update_data(subcategory=None)
    data = await state.get_data()
    category = data.get('category')
    if category in ('soft', 'bedroom'):
        await callback.message.answer("Выберите страну производства:", reply_markup=get_country_kb())
        await state.set_state(ProductForm.waiting_for_country)
    elif category in ('kitchen'):
        await callback.message.answer("Выберите тип товара:", reply_markup=get_type_kb())
        await state.set_state(ProductForm.waiting_for_type)
    else:
        await callback.message.answer("Введите размеры товара:", reply_markup=get_skip_cancel_kb())
        await state.set_state(ProductForm.waiting_for_sizes)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_category, F.data == "add_cancel")
async def cancel_add_product_subcategory(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Callback для выбора страны
@router.callback_query(ProductForm.waiting_for_country, F.data.startswith("country_"))
async def add_product_country(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data.get('category')
    country = None
    if callback.data == "country_skip_country":
        await state.update_data(country=None)
    elif callback.data == "country_cancel_country":
        await callback.message.delete()
        await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
        await state.clear()
        await callback.answer()
        return
    else:
        country = callback.data.replace("country_", "")
        await state.update_data(country=country)
    # Тип только для мягкой мебели (если страна не Турция) и для кухни
    if (category == 'soft' and country != 'turkey') or category == 'kitchen':
        await callback.message.answer("Выберите тип товара:", reply_markup=get_type_kb())
        await state.set_state(ProductForm.waiting_for_type)
    else:
        await callback.message.answer("Введите размеры товара:", reply_markup=get_skip_cancel_kb())
        await state.set_state(ProductForm.waiting_for_sizes)
    await callback.answer()

# Callback для выбора типа
@router.callback_query(ProductForm.waiting_for_type, F.data.startswith("type_"))
async def add_product_type(callback: CallbackQuery, state: FSMContext):
    if callback.data == "type_skip_type":
        await state.update_data(type=None)
    elif callback.data == "type_cancel_type":
        await callback.message.delete()
        await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
        await state.clear()
        await callback.answer()
        return
    else:
        type_ = callback.data.replace("type_", "")
        await state.update_data(type=type_)
    await callback.message.answer("Введите размеры товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_sizes)
    await callback.answer()

# Обработка размеров товара
@router.message(ProductForm.waiting_for_sizes)
async def add_product_sizes(message: Message, state: FSMContext):
    await state.update_data(sizes=message.text)
    await message.answer("Введите цену товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_price)

# Callback для пропуска размеров
@router.callback_query(ProductForm.waiting_for_sizes, F.data == "add_skip")
async def skip_sizes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sizes=None)
    await callback.message.answer("Введите цену товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_price)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_sizes, F.data == "add_cancel")
async def cancel_add_product_sizes(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Обработка цены товара
@router.message(ProductForm.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Введите описание товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_description)

# Callback для пропуска цены
@router.callback_query(ProductForm.waiting_for_price, F.data == "add_skip")
async def skip_price(callback: CallbackQuery, state: FSMContext):
    await state.update_data(price=None)
    await callback.message.answer("Введите описание товара:", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_description)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_price, F.data == "add_cancel")
async def cancel_add_product_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Обработка описания товара
@router.message(ProductForm.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Отправьте фото товара (или пропустите этот шаг):", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_images)

# Callback для пропуска описания
@router.callback_query(ProductForm.waiting_for_description, F.data == "add_skip")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await callback.message.answer("Отправьте фото товара (или пропустите этот шаг):", reply_markup=get_skip_cancel_kb())
    await state.set_state(ProductForm.waiting_for_images)
    await callback.answer()

# Callback для отмены добавления товара
@router.callback_query(ProductForm.waiting_for_description, F.data == "add_cancel")
async def cancel_add_product_description(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Обработка фото товара
@router.message(ProductForm.waiting_for_images)
async def add_product_images(message: Message, state: FSMContext):
    images = await state.get_data()
    images_list = images.get("images", [])
    if message.photo:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_path = f"media/product_{photo.file_id}.jpg"
        await message.bot.download_file(file.file_path, file_path)
        images_list.append(file_path)
    await state.update_data(images=images_list)
    await message.answer("Фото добавлено. Отправьте ещё фото или нажмите '✅ Готово' для завершения.", reply_markup=get_images_done_kb())

# Callback для завершения добавления фото
@router.callback_query(ProductForm.waiting_for_images, F.data == "images_done")
async def finish_images(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    images_str = ";".join(images) if images else None
    await state.update_data(images=images_str)
    text = "<b>Проверьте введённые данные:</b>\n"
    for key, value in data.items():
        text += f"<b>{key}</b>: {value}\n"
    await callback.message.answer(text, reply_markup=get_confirm_add_kb(), parse_mode="HTML")
    await state.set_state(ProductForm.waiting_for_final_confirm)
    await callback.answer()

# Callback для отмены добавления фото
@router.callback_query(ProductForm.waiting_for_images, F.data == "add_cancel")
async def cancel_add_product_images(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

# Callback для подтверждения добавления товара
@router.callback_query(ProductForm.waiting_for_final_confirm, F.data == "add_confirm")
async def add_product_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        await add_product(session, **data)
    await callback.message.answer("Товар успешно добавлен!")
    await state.clear()
    await callback.answer()

# Callback для отмены добавления товара на финальном шаге
@router.callback_query(ProductForm.waiting_for_final_confirm, F.data == "add_cancel")
async def add_product_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("⚙️ Админская панель", reply_markup=admin_main_kb)
    await state.clear()
    await callback.answer()

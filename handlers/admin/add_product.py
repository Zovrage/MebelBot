from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import os
import time

from keyboards.admin.add_product import (
    get_category_kb, get_country_kb, get_type_kb,
    get_images_done_kb
)
from states.admin import ProductForm
from database.db import async_session
from database.crud import add_product, add_photo, update_product
from database.models import ProductCategory

router = Router()

MEDIA_DIR = os.path.join(os.getcwd(), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

# Начало добавления товара (строго пошагово)
@router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Введите название товара:")
    await state.set_state(ProductForm.waiting_for_name)
    await callback.answer()

@router.message(ProductForm.waiting_for_name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Выберите категорию:", reply_markup=get_category_kb())
    await state.set_state(ProductForm.waiting_for_category)

@router.callback_query(ProductForm.waiting_for_category, F.data.startswith("category_"))
async def add_choose_category(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("category_", "")
    try:
        category = ProductCategory[code]
    except Exception:
        category = code
    await state.update_data(category=category)
    await callback.message.answer("Введите подкатегорию (при необходимости, иначе напишите -):")
    await state.set_state(ProductForm.waiting_for_subcategory)
    await callback.answer()

@router.message(ProductForm.waiting_for_subcategory)
async def add_subcategory(message: Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    await message.answer("Выберите страну производства:", reply_markup=get_country_kb())
    await state.set_state(ProductForm.waiting_for_country)

@router.callback_query(ProductForm.waiting_for_country, F.data.startswith("country_"))
async def add_choose_country(callback: CallbackQuery, state: FSMContext):
    country = callback.data.replace("country_", "")
    if country in ("skip_country", "cancel_country"):
        country = "-"
    await state.update_data(country=country)
    await callback.message.answer("Выберите тип:", reply_markup=get_type_kb())
    await state.set_state(ProductForm.waiting_for_type)
    await callback.answer()

@router.callback_query(ProductForm.waiting_for_type, F.data.startswith("type_"))
async def add_choose_type(callback: CallbackQuery, state: FSMContext):
    type_code = callback.data.replace("type_", "")
    if type_code in ("skip_type", "cancel_type"):
        type_code = "-"
    await state.update_data(type=type_code)
    await callback.message.answer("Введите цену (только цифры, можно с точкой):")
    await state.set_state(ProductForm.waiting_for_price)
    await callback.answer()

@router.message(ProductForm.waiting_for_price)
async def add_price(message: Message, state: FSMContext):
    text = message.text.replace(" ", "")
    try:
        price = float(text)
    except Exception:
        await message.answer("Неверный формат цены. Введите цифры, можно с точкой.")
        return
    await state.update_data(price=price)
    await message.answer("Отправьте фото товара (можно несколько). Нажмите '✅ Готово' когда закончите.", reply_markup=get_images_done_kb())
    await state.update_data(images=[])
    await state.set_state(ProductForm.waiting_for_images)

@router.message(ProductForm.waiting_for_images, F.content_type == "photo")
async def add_images_receive(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ts = int(time.time() * 1000)
    filename = f"product_tmp_{ts}_{photo.file_id}.jpg"
    file_path = os.path.join(MEDIA_DIR, filename)
    await message.bot.download_file(file.file_path, file_path)
    data = await state.get_data() or {}
    images = data.get("images", []) or []
    images.append(file_path)
    await state.update_data(images=images)
    await message.answer("Фото принято. Можете отправить ещё или нажать '✅ Готово'.", reply_markup=get_images_done_kb())

@router.callback_query(ProductForm.waiting_for_images, F.data == "images_done")
async def images_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data() or {}
    name = data.get("name")
    category = data.get("category")
    subcategory = data.get("subcategory")
    country = data.get("country")
    type_ = data.get("type")
    price = data.get("price")
    images = data.get("images", []) or []

    if not name:
        await callback.message.answer("Нельзя сохранить товар без названия. Укажите название.")
        await callback.answer()
        return

    if isinstance(category, ProductCategory):
        category_val = category
    else:
        try:
            category_val = ProductCategory[category]
        except Exception:
            category_val = category

    async with async_session() as session:
        product = await add_product(
            session,
            name=name,
            category=category_val,
            subcategory=subcategory,
            country=country,
            type=type_,
            price=price
        )
        saved_paths = []
        for idx, img in enumerate(images, start=1):
            if os.path.isfile(img):
                ext = os.path.splitext(img)[1] or '.jpg'
                final_name = f"product_{product.id}_{idx}{ext}"
                final_path = os.path.join(MEDIA_DIR, final_name)
                try:
                    os.replace(img, final_path)
                except Exception:
                    try:
                        import shutil
                        shutil.copy(img, final_path)
                        os.remove(img)
                    except Exception:
                        final_path = img
                saved_paths.append(final_path)
                await add_photo(session, product.id, final_path)
        if saved_paths:
            images_field = ';'.join(saved_paths)
            await update_product(session, product.id, images=images_field)

    await callback.message.answer("Товар успешно добавлен.")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "add_cancel")
async def add_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Добавление товара отменено.")
    await callback.answer()

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from states.admin import ProductForm
from keyboards.admin import get_admin_main_kb, get_add_product_step_kb, get_categories_kb
from config import ADMIN_IDS
from database.models import ProductCategory
from database.db import async_session
from database.crud import add_product, add_photo
import os
import uuid
from aiogram.filters import StateFilter

router = Router()

# --- Проверка администратора ---
def is_admin(user_id):
    return user_id in ADMIN_IDS


@router.callback_query(F.data == 'admin_back_main')
async def admin_back_main(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    await call.message.edit_text('Админ-панель', reply_markup=get_admin_main_kb())

# --- Добавление товара ---
@router.callback_query(F.data == 'admin_add_product')
async def admin_add_product(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    await call.message.answer('Введите название товара:', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_name)

@router.message(ProductForm.waiting_for_name)
async def admin_product_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer('Выберите категорию:', reply_markup=get_categories_kb())
    await state.set_state(ProductForm.waiting_for_category)

@router.callback_query(StateFilter(ProductForm.waiting_for_category), F.data.startswith('admin_cat_'))
async def admin_product_category_callback(call: CallbackQuery, state: FSMContext):
    cat_name = call.data.replace('admin_cat_', '')
    await state.update_data(category=cat_name)
    await call.message.edit_text('Введите подкатегорию (страна, тип и т.д.):', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_subcategory)

@router.message(ProductForm.waiting_for_subcategory)
async def admin_product_subcategory(msg: Message, state: FSMContext):
    await state.update_data(subcategory=msg.text)
    await msg.answer('Страна производства:', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_country)

@router.message(ProductForm.waiting_for_country)
async def admin_product_country(msg: Message, state: FSMContext):
    await state.update_data(country=msg.text)
    await msg.answer('Тип (прямая, угловая и т.д.):', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_type)

@router.message(ProductForm.waiting_for_type)
async def admin_product_type(msg: Message, state: FSMContext):
    await state.update_data(type=msg.text)
    await msg.answer('Цена:', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_price)

@router.message(ProductForm.waiting_for_price)
async def admin_product_price(msg: Message, state: FSMContext):
    try:
        price = float(msg.text)
    except ValueError:
        await msg.answer('Введите число (цена):', reply_markup=get_add_product_step_kb())
        return
    await state.update_data(price=price)
    await msg.answer('Описание:', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_description)

@router.message(ProductForm.waiting_for_description)
async def admin_product_description(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer('Введите размеры товара (например, 200x80x40 см):', reply_markup=get_add_product_step_kb())
    await state.set_state(ProductForm.waiting_for_sizes)

@router.message(ProductForm.waiting_for_sizes)
async def admin_product_sizes(msg: Message, state: FSMContext):
    await state.update_data(sizes=msg.text)
    await msg.answer('Отправьте 1-5 фото товара (по одному сообщению, когда закончите — напишите "Готово"):')
    await state.set_state(ProductForm.waiting_for_images)
    await state.update_data(images=[])

@router.message(ProductForm.waiting_for_images, F.photo)
async def admin_product_image(msg: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get('images', [])
    if len(images) >= 5:
        await msg.answer('Максимум 5 фото. Напишите "Готово" если закончили.')
        return
    file_id = msg.photo[-1].file_id
    images.append(file_id)
    await state.update_data(images=images)
    await msg.answer(f'Фото добавлено ({len(images)}/5). Ещё фото или "Готово".')

@router.message(ProductForm.waiting_for_images, F.text.lower() == 'готово')
async def admin_product_images_done(msg: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get('images', [])
    async with async_session() as session:
        product = await add_product(session,
            name=data['name'],
            category=data['category'],
            subcategory=data['subcategory'],
            country=data['country'],
            type=data['type'],
            price=data['price'],
            description=data['description'],
            sizes=data.get('sizes'),
            images=None  # images теперь не нужны
        )
        # Сохраняем фото в media и записываем в Photo
        for idx, file_id in enumerate(images):
            file = await msg.bot.get_file(file_id)
            ext = os.path.splitext(file.file_path)[-1] or '.jpg'
            filename = f"product_{product.id}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join('media', filename)
            await msg.bot.download_file(file.file_path, file_path)
            await add_photo(session, product_id=product.id, filename=filename, original_file_id=file_id)
    await msg.answer('Товар добавлен!', reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == 'cancel_add')
async def cancel_add_product(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(F.data == 'skip_add')
async def skip_add_product(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()
    # Переход к следующему шагу, сохраняя None
    if current_state == ProductForm.waiting_for_name.state:
        await state.update_data(name=None)
        cats = [c.value for c in ProductCategory]
        await call.message.answer(f'Выберите категорию:')
        await state.set_state(ProductForm.waiting_for_category)
    elif current_state == ProductForm.waiting_for_category.state:
        await state.update_data(category=None)
        await call.message.answer('Введите подкатегорию (страна, тип и т.д.):')
        await state.set_state(ProductForm.waiting_for_subcategory)
    elif current_state == ProductForm.waiting_for_subcategory.state:
        await state.update_data(subcategory=None)
        await call.message.answer('Страна производства:')
        await state.set_state(ProductForm.waiting_for_country)
    elif current_state == ProductForm.waiting_for_country.state:
        await state.update_data(country=None)
        await call.message.answer('Тип (прямая, угловая и т.д.):')
        await state.set_state(ProductForm.waiting_for_type)
    elif current_state == ProductForm.waiting_for_type.state:
        await state.update_data(type=None)
        await call.message.answer('Цена:')
        await state.set_state(ProductForm.waiting_for_price)
    elif current_state == ProductForm.waiting_for_price.state:
        await state.update_data(price=None)
        await call.message.answer('Описание:')
        await state.set_state(ProductForm.waiting_for_description)
    elif current_state == ProductForm.waiting_for_description.state:
        await state.update_data(description=None)
        await call.message.answer('Введите размеры товара (например, 200x80x40 см):')
        await state.set_state(ProductForm.waiting_for_sizes)
    elif current_state == ProductForm.waiting_for_sizes.state:
        await state.update_data(sizes=None)
        await call.message.answer('Отправьте 1-5 фото товара (по одному сообщению, когда закончите — напишите "Готово"):')
        await state.set_state(ProductForm.waiting_for_images)
    elif current_state == ProductForm.waiting_for_images.state:
        await state.update_data(images=None)
        # Завершить добавление, если фото пропущены
        async with async_session() as session:
            await add_product(session,
                name=data.get('name'),
                category=data.get('category'),
                subcategory=data.get('subcategory'),
                country=data.get('country'),
                type=data.get('type'),
                price=data.get('price'),
                description=data.get('description'),
                sizes=None,
                images=None
            )
        await call.message.answer('Товар добавлен (без фото).', reply_markup=get_admin_main_kb())
        await state.clear()

@router.callback_query(ProductForm.waiting_for_name, F.data == 'cancel_add')
async def cancel_add_name(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_category, F.data == 'cancel_add')
async def cancel_add_category(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_subcategory, F.data == 'cancel_add')
async def cancel_add_subcategory(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_country, F.data == 'cancel_add')
async def cancel_add_country(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_type, F.data == 'cancel_add')
async def cancel_add_type(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_price, F.data == 'cancel_add')
async def cancel_add_price(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_description, F.data == 'cancel_add')
async def cancel_add_description(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_images, F.data == 'cancel_add')
async def cancel_add_images(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Добавление товара отменено.', reply_markup=get_admin_main_kb())

@router.callback_query(ProductForm.waiting_for_name, F.data == 'skip_add')
async def skip_add_name(call: CallbackQuery, state: FSMContext):
    await state.update_data(name=None)
    cats = [c.value for c in ProductCategory]
    await call.message.answer(f'Выберите категорию:')
    await state.set_state(ProductForm.waiting_for_category)

@router.callback_query(ProductForm.waiting_for_category, F.data == 'skip_add')
async def skip_add_category(call: CallbackQuery, state: FSMContext):
    await state.update_data(category=None)
    await call.message.answer('Введите подкатегорию (страна, тип и т.д.):')
    await state.set_state(ProductForm.waiting_for_subcategory)

@router.callback_query(ProductForm.waiting_for_subcategory, F.data == 'skip_add')
async def skip_add_subcategory(call: CallbackQuery, state: FSMContext):
    await state.update_data(subcategory=None)
    await call.message.answer('Страна производства:')
    await state.set_state(ProductForm.waiting_for_country)

@router.callback_query(ProductForm.waiting_for_country, F.data == 'skip_add')
async def skip_add_country(call: CallbackQuery, state: FSMContext):
    await state.update_data(country=None)
    await call.message.answer('Тип (прямая, угловая и т.д.):')
    await state.set_state(ProductForm.waiting_for_type)

@router.callback_query(ProductForm.waiting_for_type, F.data == 'skip_add')
async def skip_add_type(call: CallbackQuery, state: FSMContext):
    await state.update_data(type=None)
    await call.message.answer('Цена:')
    await state.set_state(ProductForm.waiting_for_price)

@router.callback_query(ProductForm.waiting_for_price, F.data == 'skip_add')
async def skip_add_price(call: CallbackQuery, state: FSMContext):
    await state.update_data(price=None)
    await call.message.answer('Описание:')
    await state.set_state(ProductForm.waiting_for_description)

@router.callback_query(ProductForm.waiting_for_description, F.data == 'skip_add')
async def skip_add_description(call: CallbackQuery, state: FSMContext):
    await state.update_data(description=None)
    await call.message.answer('Введите размеры товара (например, 200x80x40 см):')
    await state.set_state(ProductForm.waiting_for_sizes)

@router.callback_query(ProductForm.waiting_for_sizes, F.data == 'skip_add')
async def skip_add_sizes(call: CallbackQuery, state: FSMContext):
    await state.update_data(sizes=None)
    await call.message.answer('Отправьте 1-5 фото товара (по одному сообщению, когда закончите — напишите "Готово"):')
    await state.set_state(ProductForm.waiting_for_images)

@router.callback_query(StateFilter(ProductForm.waiting_for_name))
async def ask_name_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите название товара:')

@router.callback_query(StateFilter(ProductForm.waiting_for_category))
async def ask_category_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Выберите категорию:')

@router.callback_query(StateFilter(ProductForm.waiting_for_subcategory))
async def ask_subcategory_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите подкатегорию (страна, тип и т.д.):')

@router.callback_query(StateFilter(ProductForm.waiting_for_country))
async def ask_country_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Страна производства:')

@router.callback_query(StateFilter(ProductForm.waiting_for_type))
async def ask_type_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Тип (прямая, угловая и т.д.):')

@router.callback_query(StateFilter(ProductForm.waiting_for_price))
async def ask_price_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Цена:')

@router.callback_query(StateFilter(ProductForm.waiting_for_description))
async def ask_description_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Описание:')

@router.callback_query(StateFilter(ProductForm.waiting_for_images))
async def ask_images_step(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Отправьте 1-5 фото товара (по одному сообщению, когда закончите — напишите "Готово"):')
@router.callback_query(F.data == 'admin_manage_products')
async def admin_manage_products(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Нет доступа', show_alert=True)
        return
    from keyboards.admin import get_admin_categories_kb
    await call.message.edit_text('Выберите категорию:', reply_markup=get_admin_categories_kb())

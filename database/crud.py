from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload
from .models import Product, Lead, LeadStatus, ProductCategory, Photo

# --- CRUD для товаров ---
async def add_product(session: AsyncSession, **kwargs):
    product = Product(**kwargs)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

async def get_products(session: AsyncSession, category=None, country=None, type_=None):
    stmt = select(Product)
    if category:
        if isinstance(category, str):
            category = ProductCategory(category)
        stmt = stmt.where(Product.category == category)
    if country:
        stmt = stmt.where(Product.country == country)
    if type_:
        stmt = stmt.where(Product.type == type_)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_product(session: AsyncSession, product_id):
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def update_product(session: AsyncSession, product_id, update_data: dict, new_photos: list = None, delete_photo_ids: list = None):
    # Обновление полей товара
    await session.execute(update(Product).where(Product.id == product_id).values(**update_data))
    # Удаление фото
    if delete_photo_ids:
        await session.execute(delete(Photo).where(Photo.id.in_(delete_photo_ids), Photo.product_id == product_id))
    # Добавление новых фото
    if new_photos:
        for photo_data in new_photos:
            photo = Photo(product_id=product_id, **photo_data)
            session.add(photo)
    await session.commit()

async def delete_product(session: AsyncSession, product_id):
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()

# --- CRUD для фото ---
async def add_photo(session: AsyncSession, product_id: int, filename: str, original_file_id: str = None):
    photo = Photo(product_id=product_id, filename=filename, original_file_id=original_file_id)
    session.add(photo)
    await session.commit()
    await session.refresh(photo)
    return photo

async def delete_photo(session: AsyncSession, photo_id: int):
    await session.execute(delete(Photo).where(Photo.id == photo_id))
    await session.commit()

async def get_photos_by_product(session: AsyncSession, product_id: int):
    result = await session.execute(select(Photo).where(Photo.product_id == product_id))
    return result.scalars().all()

# --- CRUD для заявок (лидов) ---
async def add_lead(session: AsyncSession, **kwargs):
    lead = Lead(**kwargs)
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead

async def get_leads(session: AsyncSession, status=None):
    stmt = select(Lead).options(selectinload(Lead.product))
    if status:
        if isinstance(status, str):
            status = LeadStatus(status)
        stmt = stmt.where(Lead.status == status)
    result = await session.execute(stmt)
    return result.scalars().all()

async def update_lead_status(session: AsyncSession, lead_id, status: LeadStatus):
    if isinstance(status, str):
        status = LeadStatus(status)
    await session.execute(update(Lead).where(Lead.id == lead_id).values(status=status))
    await session.commit()

async def delete_lead(session: AsyncSession, lead_id):
    await session.execute(delete(Lead).where(Lead.id == lead_id))
    await session.commit()

# --- CRUD для фотографий товаров ---
async def add_photo(session: AsyncSession, product_id: int, filename: str, original_file_id: str = None):
    photo = Photo(product_id=product_id, filename=filename, original_file_id=original_file_id)
    session.add(photo)
    await session.commit()
    await session.refresh(photo)
    return photo

async def get_photos_by_product(session: AsyncSession, product_id: int):
    result = await session.execute(select(Photo).where(Photo.product_id == product_id))
    return result.scalars().all()

async def delete_photo(session: AsyncSession, photo_id: int):
    await session.execute(delete(Photo).where(Photo.id == photo_id))
    await session.commit()

async def get_products_by_params(category=None, country=None, type_=None):
    from .db import async_session
    async with async_session() as session:
        stmt = select(Product)
        if category:
            enum_category = None
            if isinstance(category, str):
                # Пробуем получить enum по имени (например 'soft')
                try:
                    enum_category = ProductCategory[category]
                except Exception:
                    # Если не получилось, не ищем по значению, а фильтруем по строке
                    enum_category = category
            else:
                enum_category = category
            stmt = stmt.where(Product.category == enum_category)
        if country:
            stmt = stmt.where(Product.country == country)
        if type_:
            stmt = stmt.where(Product.type == type_)
        result = await session.execute(stmt)
        return result.scalars().all()

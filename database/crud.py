from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from .models import Product, Lead, LeadStatus, ProductCategory, Photo

# --- CRUD для товаров ---
async def add_product(session: AsyncSession, **kwargs):
    product = Product(**kwargs)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

async def get_products(session: AsyncSession, category=None, country=None, type_=None):
    from .models import ProductCategory
    from sqlalchemy import Enum as SqlEnum
    stmt = select(Product)
    if category:
        if isinstance(category, str):
            try:
                category = ProductCategory[category]
            except Exception:
                pass
        stmt = stmt.where(Product.category == category)
    if country:
        if isinstance(Product.country.type, SqlEnum):
            try:
                country = Product.country.type.enum_class[country]
            except Exception:
                pass
        stmt = stmt.where(Product.country == country)
    if type_:
        if isinstance(Product.type.type, SqlEnum):
            try:
                type_ = Product.type.type.enum_class[type_]
            except Exception:
                pass
        stmt = stmt.where(Product.type == type_)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_all_products(session: AsyncSession):
    return await get_products(session)

async def get_product(session: AsyncSession, product_id):
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def update_product(session: AsyncSession, product_id, **kwargs):
    await session.execute(update(Product).where(Product.id == product_id).values(**kwargs))
    await session.commit()

async def delete_product(session: AsyncSession, product_id):
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()

async def get_products_paginated(session: AsyncSession, offset=0, limit=5, category=None, country=None, type_=None):
    from database.models import Product, ProductCategory
    stmt = select(Product)
    if category:
        if isinstance(category, str):
            category = ProductCategory(category)
        stmt = stmt.where(Product.category == category)
    if country:
        stmt = stmt.where(Product.country == country)
    if type_:
        stmt = stmt.where(Product.type == type_)
    stmt = stmt.order_by(Product.id.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    products = result.scalars().all()
    # Получить общее количество товаров
    total_stmt = select(Product)
    if category:
        total_stmt = total_stmt.where(Product.category == category)
    if country:
        total_stmt = total_stmt.where(Product.country == country)
    if type_:
        total_stmt = total_stmt.where(Product.type == type_)
    total = await session.execute(total_stmt)
    total_count = len(total.scalars().all())
    return products, total_count

# --- CRUD для заявок (лидов) ---
async def add_lead(session: AsyncSession, **kwargs):
    lead = Lead(**kwargs)
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead

async def get_leads(session: AsyncSession, status=None):
    stmt = select(Lead)
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

async def get_products_by_category(category, country=None, type_=None):
    """
    Возвращает список товаров по категории, стране и типу (для управления товарами).
    """
    from .db import async_session
    async with async_session() as session:
        products = await get_products(session, category=category, country=country, type_=type_)
        # Приводим к списку словарей для удобства вывода
        return [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'country': p.country,
                'type': p.type,
                'sizes': p.sizes,
                'price': p.price,
                'images': p.images,
                'subcategory': p.subcategory,
                'category': p.category.value if hasattr(p.category, 'value') else p.category
            }
            for p in products
        ]

async def update_product_photo(session: AsyncSession, product_id, file_path, file_id=None):
    product = await get_product(session, product_id)
    if product:
        # Если уже есть фото, заменяем. Можно добавить, если нужно хранить несколько фото.
        product.images = file_path
        await session.commit()
        await session.refresh(product)
        return product
    return None

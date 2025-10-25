import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from .db import Base

# Категории товаров
class ProductCategory(enum.Enum):
    bedroom = 'bedroom'
    kitchen = 'kitchen'
    soft = 'soft'
    tables = 'tables'
    dressers = 'dressers'
    beds = 'beds'
    mattress = 'mattress'
    wardrobe = 'wardrobe'

# Словарь для отображения категорий на русском
CATEGORY_DISPLAY = {
    ProductCategory.bedroom: 'Спальная мебель',
    ProductCategory.kitchen: 'Кухонная мебель',
    ProductCategory.soft: 'Мягкая мебель',
    ProductCategory.tables: 'Столы и стулья',
    ProductCategory.dressers: 'Тумбы и комоды',
    ProductCategory.beds: 'Кровати',
    ProductCategory.mattress: 'Матрасы',
    ProductCategory.wardrobe: 'Шкафы',
}


# Товар
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    subcategory = Column(String(255), nullable=True)  # страна, тип, форма и т.д.
    country = Column(String(100), nullable=True)
    type = Column(String(100), nullable=True)  # прямая, угловая и т.д.
    price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    sizes = Column(String(255), nullable=True)  # Размеры товара
    photos = relationship('Photo', back_populates='product', cascade='all, delete-orphan')

# Статус заявки (лида)
class LeadStatus(enum.Enum):
    new = 'Новая'
    in_progress = 'В работе'
    closed = 'Закрыта'

#  Заявка (лид)
class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    comment = Column(Text, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    product = relationship('Product')

# Фотография товара
class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False)  # путь к файлу в media
    original_file_id = Column(String(255), nullable=True)  # file_id Telegram
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship('Product', back_populates='photos')

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from .db import Base


class ProductCategory(enum.Enum):
    bedroom = 'Спальная мебель'
    kitchen = 'Кухонная мебель'
    soft = 'Мягкая мебель'
    bed = 'Кровати'
    tables = 'Столы и стулья'
    dressers = 'Тумбы и комоды'
    mattress = 'Матрасы'
    wardrobe = 'Шкафы'


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
    images = Column(Text, nullable=True)  # Список путей через ;
    sizes = Column(String(255), nullable=True)  # Размеры товара


class LeadStatus(enum.Enum):
    new = 'Новая'
    in_progress = 'В работе'
    closed = 'Закрыта'


class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    comment = Column(Text, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    product = relationship('Product')


class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    filename = Column(String(255), nullable=False)  # путь к файлу в media
    original_file_id = Column(String(255), nullable=True)  # file_id Telegram
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship('Product', backref='photos')

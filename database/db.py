import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base





# Абсолютный путь к БД — работает независимо от того, откуда запущен бот
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # корень проекта
DB_PATH = os.path.join(BASE_DIR, 'database', "DataBase.db")
# Абсолютный путь к БД
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


# Создание асинхронного движка базы данных
engine = create_async_engine(DATABASE_URL, echo=True, future=True)


# Создание базового класса для моделей
Base = declarative_base()


# Создание асинхронной сессии
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Функция для инициализации базы данных (создание всех таблиц)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Получение сессии
async def get_session():
    async with async_session() as session:
        yield session
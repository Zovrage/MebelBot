import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import router
from database.db import init_db



# Основная асинхронная функция для запуска бота
async def main():
    if not os.path.exists('media'):
        os.makedirs('media')
    await init_db()
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    # Точка входа в приложение. Запускает асинхронную функцию main.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выход")
    except Exception as e:
        print(f"Ошибка: {e}")


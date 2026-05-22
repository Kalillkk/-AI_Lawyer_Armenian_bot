import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import start, legal, payment, admin

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    init_db()
    
    # Создаём бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключаем handlers
    dp.include_router(start.router)
    dp.include_router(legal.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Запускаем бота
    print("🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
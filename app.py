import asyncio
import os
import logging
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import start, legal, payment, admin

# Flask приложение
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return "OK", 200

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
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
        logger.info("🤖 Telegram бот запущен и готов к работе!")
        asyncio.run(dp.start_polling(bot))
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def run_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    logger.info("🚀 Запуск сервиса...")
    
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Запускаем Flask в основном потоке
    run_flask()
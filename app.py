import asyncio
import os
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI

# Flask приложение для поддержки работы хостинга
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

# Telegram бот
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1") if OPENAI_API_KEY else None

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("⚖️ Привет! Я юридический AI-помощник. Задайте ваш вопрос.")

@dp.message()
async def answer(message: types.Message):
    if not ai_client:
        await message.answer("API не настроен")
        return
    
    try:
        response = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты юридический помощник"},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer("Ошибка, попробуйте позже")

def run_bot():
    asyncio.run(dp.start_polling(bot))

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    thread = Thread(target=run_flask)
    thread.start()
    run_bot()
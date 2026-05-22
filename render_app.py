import asyncio
import os
import logging
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Flask приложение
app = Flask(__name__)

@app.route('/')
def health():
    return "🤖 AI Lawyer Bot is running!", 200

@app.route('/health')
def health_check():
    return "OK", 200

# Telegram бот
if not BOT_TOKEN or not OPENAI_API_KEY:
    print("❌ Missing environment variables")
else:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1")
    
    SYSTEM_PROMPT = """Դու իրավական AI օգնական ես:
    Պատասխանիր ՆՈՒՅՆ լեզվով, ինչ հարցը:
    Նախազգուշացրու, որ դու պրոֆեսիոնալ իրավաբան ՉԵՍ:"""
    
    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer(
            "⚖️ **Բարի գալուստ / Добро пожаловать / Welcome!**\n\n"
            "📌 Տվեք ձեր հարցը - կպատասխանեմ նույն լեզվով\n"
            "⚠️ Ես պրոֆեսիոնալ իրավաբան ՉԵՄ",
            parse_mode="Markdown"
        )
    
    @dp.message()
    async def handle(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")
        try:
            response = await ai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
                temperature=0.7,
                max_tokens=1000
            )
            await message.answer(response.choices[0].message.content)
        except Exception as e:
            await message.answer("❌ Տեխնիկական սխալ / Техническая ошибка")
    
    async def run_bot():
        print("🤖 Бот запущен на Render!")
        await dp.start_polling(bot)
    
    def start_bot_thread():
        asyncio.run(run_bot())
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=start_bot_thread)
    bot_thread.start()

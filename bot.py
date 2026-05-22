import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Missing BOT_TOKEN or OPENAI_API_KEY in .env")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1")

SYSTEM_PROMPT = """You are a legal AI assistant. Answer in the same language as the user's question (Armenian, Russian, or English). Warn that you are not a professional lawyer. Provide references to laws if possible."""

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚖️ **Բարի գալուստ / Добро пожаловать / Welcome!**\n\n"
        "Ուղարկեք ձեր իրավական հարցը:\n"
        "Отправьте ваш юридический вопрос:\n"
        "Send your legal question:\n\n"
        "⚠️ Ես պրոֆեսիոնալ իրավաբան ՉԵՄ",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("/start - Начать / Սկիզբ\n/help - Помощь / Օգնություն")

@dp.message()
async def handle(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    try:
        resp = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        await message.answer(resp.choices[0].message.content)
    except Exception as e:
        logging.error(e)
        await message.answer("❌ Տեխնիկական սխալ / Техническая ошибка")

async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

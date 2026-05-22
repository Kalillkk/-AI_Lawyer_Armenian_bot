import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверяем наличие токенов
if not BOT_TOKEN:
    print("ОШИБКА: BOT_TOKEN не найден")
    exit(1)
if not OPENAI_API_KEY:
    print("ОШИБКА: OPENAI_API_KEY не найден. Добавьте его в файл .env")
    exit(1)

# Настройки
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1")

# Системный промпт для юридического помощника
SYSTEM_PROMPT = """Ты - юридический AI-помощник. Твоя задача:
1. Отвечать на юридические вопросы четко и по делу
2. Предупреждать, что ты не заменяет профессионального юриста
3. Использовать законодательство РФ и международное право
4. Давать ссылки на соответствующие законы, если возможно"""

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        "⚖️ Здравствуйте! Я юридический AI-помощник.\n\n"
        "Задайте ваш юридический вопрос, и я постараюсь помочь.\n\n"
        "⚠️ ВАЖНО: Я не заменяю профессионального юриста. "
        "Для серьезных дел обязательно консультируйтесь со специалистом."
    )

@dp.message()
async def handle_question(message: Message):
    # Показываем статус "печатает"
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Отправляем запрос к ИИ
        response = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Бесплатная модель Groq
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        await message.answer(answer)
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer(
            "Извините, произошла ошибка. Пожалуйста, попробуйте позже.\n"
            "Если ошибка повторяется, обратитесь к администратору."
        )

@dp.message(Command("help"))
async def send_help(message: Message):
    await message.answer(
        "📋 Доступные команды:\n"
        "/start - Начать диалог\n"
        "/help - Показать эту справку\n\n"
        "Просто отправьте ваш юридический вопрос текстовым сообщением."
    )

async def main():
    print("🤖 Юридический AI-бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
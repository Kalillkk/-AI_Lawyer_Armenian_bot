import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверяем наличие токенов
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в файле .env")
    print("📝 Создайте файл .env со строкой: BOT_TOKEN=ваш_токен")
    exit(1)

if not OPENAI_API_KEY:
    print("❌ ОШИБКА: OPENAI_API_KEY не найден в файле .env")
    print("📝 Добавьте в .env строку: OPENAI_API_KEY=ваш_ключ_от_groq")
    exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем Groq AI
ai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Инструкция для AI
SYSTEM_PROMPT = """Դու իրավական AI օգնական ես:

ԿԱՐԵՎՈՐ: Պատասխանի՛ր ՆՈՒՅՆ լեզվով, ինչ հարցը:
- Եթե հարցը հայերեն է → պատասխանի՛ր հայերեն
- Եթե հարցը ռուսերեն է → պատասխանի՛ր ռուսերեն
- Եթե հարցը անգլերեն է → պատասխանի՛ր անգլերեն

Նախազգուշացրու, որ դու պրոֆեսիոնալ իրավաբան ՉԵՍ:
Տուր հղումներ օրենքներին, եթե հնարավոր է:"""

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "⚖️ **Բարի գալուստ / Добро пожаловать / Welcome!**\n\n"
        "Ես իրավական AI օգնական եմ:\n"
        "Я юридический AI-помощник:\n"
        "I am a legal AI assistant:\n\n"
        "📌 **Տվեք ձեր հարցը - կպատասխանեմ նույն լեզվով**\n"
        "📌 **Задайте вопрос - отвечу на том же языке**\n"
        "📌 **Ask your question - answer in the same language**\n\n"
        "⚠️ Ես պրոֆեսիոնալ իրավաբան ՉԵՄ\n"
        "⚠️ Я НЕ профессиональный юрист\n"
        "⚠️ I am NOT a professional lawyer",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer(
        "📋 **Commands / Команды / Հրամաններ:**\n"
        "/start - Начать диалог / Սկսել երկխոսությունը\n"
        "/help - Помощь / Օգնություն\n\n"
        "Просто отправьте ваш юридический вопрос текстовым сообщением.\n"
        "Ուղղակի ուղարկեք ձեր իրավական հարցը տեքստային հաղորդագրությամբ:",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_question(message: types.Message):
    # Показываем статус "печатает"
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Отправляем запрос к Groq AI
        response = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
        logger.error(f"Ошибка: {e}")
        await message.answer(
            "❌ **Տեխնիկական սխալ / Техническая ошибка**\n\n"
            "Խնդրում ենք փորձել կրկիրբ րոպե անց\n"
            "Пожалуйста, попробуйте через минуту",
            parse_mode="Markdown"
        )

async def main():
    print("=" * 50)
    print("🤖 ЮРИДИЧЕСКИЙ AI БОТ ЗАПУЩЕН")
    print("=" * 50)
    print(f"📱 Имя бота: @{(await bot.get_me()).username}")
    print("🌐 Поддерживает: 🇦🇲 Հայերեն | 🇷🇺 Русский | 🇬🇧 English")
    print("✅ Бот готов к работе! Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n🔴 Ошибка: {e}")

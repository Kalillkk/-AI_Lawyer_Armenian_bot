cd ~/"Рабочий стол/Ai_Lawes_bot"
cat > bot_fixed.py << 'EOF'
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check tokens
errors = []
if not BOT_TOKEN:
    errors.append("❌ BOT_TOKEN not found in .env file")
if not OPENAI_API_KEY:
    errors.append("❌ OPENAI_API_KEY not found in .env file")

if errors:
    print("\n" + "="*50)
    print("🔴 ERROR: Bot cannot start!")
    print("="*50)
    for err in errors:
        print(err)
    print("\n💡 Please create .env file with:")
    print("   BOT_TOKEN=your_telegram_bot_token")
    print("   OPENAI_API_KEY=your_groq_api_key")
    print("\n📖 Get Groq API key: https://console.groq.com")
    print("="*50)
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1")

# System prompt - MULTILINGUAL
SYSTEM_PROMPT = """Դու իրավական AI օգնական ես:

ԿԱՐԵՎՈՐ. Պատասխանիր ՆՈՒՅՆ լեզվով, ինչ հարցը:
- Եթե հարցը հայերեն է → պատասխանի՛ր ՄԻԱՅՆ հայերեն
- Եթե հարցը ռուսերեն է → պատասխանի՛ր ՄԻԱՅՆ ռուսերեն
- Եթե հարցը անգլերեն է → պատասխանի՛ր ՄԻԱՅՆ անգլերեն

Նախազգուշացրու, որ դու պրոֆեսիոնալ իրավաբան չես:
Տուր հղումներ համապատասխան օրենքներին, եթե հնարավոր է:

---

Ты юридический AI помощник.

ВАЖНО: Отвечай на ТОМ ЖЕ языке, что и вопрос:
- Если вопрос на армянском → отвечай ТОЛЬКО на армянском
- Если вопрос на русском → отвечай ТОЛЬКО на русском
- Если вопрос на английском → отвечай ТОЛЬКО на английском

Предупреждай, что ты не профессиональный юрист.
Дай ссылки на законы, если возможно.

---

You are a legal AI assistant.

IMPORTANT: Answer in the SAME language as the question:
- If question is in Armenian → answer ONLY in Armenian
- If question is in Russian → answer ONLY in Russian
- If question is in English → answer ONLY in English

Warn that you are not a professional lawyer.
Provide references to relevant laws when possible."""

def detect_language(text):
    """Detect language of the message"""
    armenian_range = range(0x0530, 0x058F)
    cyrillic_range = range(0x0400, 0x0500)
    
    for char in text:
        code = ord(char)
        if code in armenian_range:
            return "🇦🇲 Armenian"
        if code in cyrillic_range:
            return "🇷🇺 Russian"
    return "🇬🇧 English"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "⚖️ **Բարի գալուստ / Добро пожаловать / Welcome!**\n\n"
        "Ես իրավական AI օգնական եմ:\n"
        "Я юридический AI-помощник:\n"
        "I am a legal AI assistant:\n\n"
        "📌 **Տվեք ձեր հարցը - կպատասխանեմ նույն լեզվով**\n"
        "📌 **Задайте вопрос - отвечу на том же языке**\n"
        "📌 **Ask your question - I will answer in the same language**\n\n"
        "⚠️ **Ես պրոֆեսիոնալ իրավաբան ՉԵՄ**\n"
        "⚠️ **Я НЕ профессиональный юрист**\n"
        "⚠️ **I am NOT a professional lawyer**\n\n"
        "🔧 **Commands / Команды / Հրամաններ:**\n"
        "/start - Վերագործարկել / Restart / Перезапуск\n"
        "/help - Օգնություն / Help / Помощь\n"
        "/language - Show language support"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer(
        "📖 **Help / Помощь / Օգնություն**\n\n"
        "• Send any legal question in Armenian, Russian, or English\n"
        "• The bot will answer in the SAME language\n"
        "• Ask about laws, rights, contracts, legal procedures\n\n"
        "⚠️ The bot is NOT a substitute for professional legal advice\n\n"
        "📞 For serious legal matters, consult a qualified lawyer",
        parse_mode="Markdown"
    )

@dp.message(Command("language"))
async def show_language(message: types.Message):
    await message.answer(
        "🌐 **Supported languages / Поддерживаемые языки / Աջակցվող լեզուներ**\n\n"
        "🇦🇲 Հայերեն (Armenian)\n"
        "🇷🇺 Русский (Russian)\n"
        "🇬🇧 English\n\n"
        "The bot automatically detects your language and responds in the same language.",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_question(message: types.Message):
    # Show typing status
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Detect language
    detected_lang = detect_language(message.text)
    logger.info(f"User: {message.from_user.id} | Language: {detected_lang} | Question: {message.text[:50]}...")
    
    try:
        # Send request to Groq AI
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
        logger.info(f"Response sent to user {message.from_user.id} in {detected_lang}")
        await message.answer(answer)
        
    except Exception as e:
        logger.error(f"Error for user {message.from_user.id}: {e}")
        error_message = (
            "❌ **Տեխնիկական սխալ**\n"
            "❌ **Техническая ошибка**\n"
            "❌ **Technical error**\n\n"
            "Խնդրում ենք փորձել կրկիր րոպե անց\n"
            "Пожалуйста, попробуйте через минуту\n"
            "Please try again in a minute"
        )
        await message.answer(error_message, parse_mode="Markdown")

async def main():
    print("\n" + "="*50)
    print("🤖 AI LEGAL BOT - STARTING...")
    print("="*50)
    print(f"📱 Bot token: {'✅ OK' if BOT_TOKEN else '❌ MISSING'}")
    print(f"🔑 Groq API key: {'✅ OK' if OPENAI_API_KEY else '❌ MISSING'}")
    print(f"🌐 Multilingual: 🇦🇲 Armenian | 🇷🇺 Russian | 🇬🇧 English")
    print("="*50)
    print("✅ Bot is running! Press Ctrl+C to stop")
    print("="*50 + "\n")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n🔴 Fatal error: {e}")
EOF

# Now run the fixed bot
python3 bot_fixed.py
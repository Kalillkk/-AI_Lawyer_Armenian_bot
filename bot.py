import asyncio
import os
import logging
from flask import Flask, request, jsonify
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import AsyncOpenAI
import google.generativeai as genai

# Flask приложение
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram бот
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация AI клиентов
# Groq (через OpenAI библиотеку)
GROQ_API_KEY = os.getenv("OPENAI_API_KEY")  # Ключ от Groq
groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
) if GROQ_API_KEY else None

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
openrouter_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
) if OPENROUTER_API_KEY else None

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
) if DEEPSEEK_API_KEY else None

# Хранилище выбранного AI для каждого пользователя
user_ai_choice = {}

# Список доступных AI моделей
AI_MODELS = {
    "groq": {
        "name": "🚀 Groq (Llama 3)",
        "client": groq_client,
        "model": "llama-3.3-70b-versatile",
        "available": bool(groq_client)
    },
    "gemini": {
        "name": "⭐ Google Gemini",
        "client": gemini_model,
        "model": None,
        "available": bool(gemini_model)
    },
    "deepseek": {
        "name": "🔍 DeepSeek V3",
        "client": deepseek_client,
        "model": "deepseek-chat",
        "available": bool(deepseek_client)
    },
    "openrouter": {
        "name": "🌐 OpenRouter (GPT-4o)",
        "client": openrouter_client,
        "model": "openai/gpt-4o-mini",
        "available": bool(openrouter_client)
    }
}

def get_ai_keyboard():
    """Клавиатура для выбора AI"""
    keyboard = []
    for key, model in AI_MODELS.items():
        if model["available"]:
            status = "✅" if user_ai_choice.get("current") == key else "⚪"
            keyboard.append([InlineKeyboardButton(
                text=f"{status} {model['name']}",
                callback_data=f"set_ai_{key}"
            )])
    
    keyboard.append([InlineKeyboardButton(
        text="ℹ️ Инфо о выбранном AI",
        callback_data="show_ai_info"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def ask_ai(ai_name: str, prompt: str, system_prompt: str = "Ты юридический помощник. Отвечай на русском языке."):
    """Отправка запроса к выбранному AI"""
    
    if ai_name not in AI_MODELS:
        return None, f"AI {ai_name} не найден"
    
    model = AI_MODELS[ai_name]
    if not model["available"]:
        return None, f"❌ {model['name']} недоступен. API ключ не настроен."
    
    try:
        if ai_name == "gemini":
            # Gemini использует другой формат
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: model["client"].generate_content(f"{system_prompt}\n\nВопрос: {prompt}")
            )
            return response.text, None
            
        elif ai_name == "groq":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content, None
            
        elif ai_name == "deepseek":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content, None
            
        elif ai_name == "openrouter":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                extra_headers={
                    "HTTP-Referer": "https://t.me/AI_Lawyer_Armenian_bot",
                    "X-Title": "AI Lawyer Bot"
                }
            )
            return response.choices[0].message.content, None
            
    except Exception as e:
        logger.error(f"Ошибка {ai_name}: {e}")
        return None, f"❌ Ошибка при запросе к {model['name']}: {str(e)[:200]}"
    
    return None, "Неизвестная ошибка"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    available_ais = [name for name, model in AI_MODELS.items() if model["available"]]
    
    if available_ais:
        user_ai_choice[user_id] = available_ais[0]  # Выбираем первый доступный AI
    
    welcome_text = (
        "⚖️ **Добро пожаловать в AI Legal Assistant!**\n\n"
        "Я помогу вам с юридическими вопросами, используя лучшие нейросети.\n\n"
        f"🤖 **Доступные AI:** {', '.join([AI_MODELS[ai]['name'] for ai in available_ais if AI_MODELS[ai]['available']])}\n\n"
        "📌 **Что я могу:**\n"
        "• Отвечать на юридические вопросы\n"
        "• Анализировать правовые ситуации\n"
        "• Помогать с документами\n\n"
        "⚠️ **Важно:** Я не заменяю профессионального юриста!\n\n"
        "👇 **Нажмите кнопку ниже, чтобы выбрать AI**"
    )
    
    await message.answer(welcome_text, reply_markup=get_ai_keyboard(), parse_mode="Markdown")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data.startswith("set_ai_"):
        ai_name = callback.data.replace("set_ai_", "")
        if ai_name in AI_MODELS and AI_MODELS[ai_name]["available"]:
            user_ai_choice[user_id] = ai_name
            await callback.message.edit_text(
                f"✅ Выбран AI: **{AI_MODELS[ai_name]['name']}**\n\n"
                f"Теперь задавайте свои юридические вопросы!",
                parse_mode="Markdown",
                reply_markup=get_ai_keyboard()
            )
        else:
            await callback.answer(f"❌ {AI_MODELS[ai_name]['name']} недоступен", show_alert=True)
    
    elif callback.data == "show_ai_info":
        current_ai = user_ai_choice.get(user_id, "не выбран")
        info = "📊 **Статус AI:**\n\n"
        for key, model in AI_MODELS.items():
            status = "✅ Доступен" if model["available"] else "❌ Не настроен"
            current = " ← текущий" if key == current_ai else ""
            info += f"• {model['name']}: {status}{current}\n"
        
        if current_ai != "не выбран" and current_ai in AI_MODELS:
            info += f"\n🎯 **Сейчас используется:** {AI_MODELS[current_ai]['name']}"
        
        await callback.answer()
        await callback.message.edit_text(info, parse_mode="Markdown", reply_markup=get_ai_keyboard())

@dp.message()
async def handle_question(message: types.Message):
    user_id = message.from_user.id
    
    # Определяем какой AI использовать
    ai_name = user_ai_choice.get(user_id)
    
    if not ai_name:
        # Если AI не выбран, предлагаем выбрать
        await message.answer(
            "🤖 **Сначала выберите AI помощника!**\n\n"
            "Нажмите на кнопку ниже, чтобы выбрать нейросеть:",
            parse_mode="Markdown",
            reply_markup=get_ai_keyboard()
        )
        return
    
    # Показываем, что бот думает
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Отправляем запрос к AI
    answer, error = await ask_ai(ai_name, message.text)
    
    if error:
        await message.answer(error)
    else:
        # Добавляем информацию о том, какой AI ответил
        ai_name_display = AI_MODELS[ai_name]["name"]
        await message.answer(
            f"{answer}\n\n---\n🤖 *Ответ сгенерирован: {ai_name_display}*",
            parse_mode="Markdown"
        )

@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "📖 **Команды бота:**\n\n"
        "/start - Начать диалог\n"
        "/help - Показать эту справку\n"
        "/ai - Сменить AI помощника\n"
        "/status - Узнать какой AI активен\n\n"
        "💡 **Совет:** Разные AI лучше отвечают на разные типы вопросов. "
        "Экспериментируйте!"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("ai"))
async def change_ai(message: types.Message):
    await message.answer(
        "🤖 **Выберите AI помощника:**",
        parse_mode="Markdown",
        reply_markup=get_ai_keyboard()
    )

@dp.message(Command("status"))
async def show_status(message: types.Message):
    user_id = message.from_user.id
    current_ai = user_ai_choice.get(user_id)
    
    if current_ai and current_ai in AI_MODELS:
        await message.answer(
            f"✅ **Текущий AI:** {AI_MODELS[current_ai]['name']}\n\n"
            f"Используйте /ai для смены AI помощника.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❓ **AI не выбран.**\n\n"
            "Используйте /ai для выбора AI помощника.",
            parse_mode="Markdown"
        )

def run_bot():
    """Запуск Telegram бота"""
    asyncio.run(dp.start_polling(bot))

def run_flask():
    """Запуск Flask сервера для Render"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    logger.info("🚀 Запуск бота с поддержкой нескольких AI...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаем бота
    run_bot()

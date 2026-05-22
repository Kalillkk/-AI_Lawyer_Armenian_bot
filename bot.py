import asyncio
import os
import logging
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from openai import AsyncOpenAI
import google.generativeai as genai
from docx import Document
import PyPDF2
from speech_recognition import Recognizer, AudioFile
import io

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
GROQ_API_KEY = os.getenv("OPENAI_API_KEY")
groq_client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
openrouter_client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1") if OPENROUTER_API_KEY else None

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_API_KEY else None

# Хранилища данных
user_ai_choice = {}  # Какой AI выбран
user_history = {}    # История диалогов
user_requests = {}   # Счётчик запросов
user_subscription = {} # Подписки через Stars
admin_id = os.getenv("ADMIN_ID")  # Ваш Telegram ID

# AI модели
AI_MODELS = {
    "groq": {
        "name": "🚀 Groq (Llama 3)",
        "client": groq_client,
        "model": "llama-3.3-70b-versatile",
        "available": bool(groq_client),
        "speed": 0
    },
    "gemini": {
        "name": "⭐ Google Gemini",
        "client": gemini_model,
        "model": None,
        "available": bool(gemini_model),
        "speed": 0
    },
    "deepseek": {
        "name": "🔍 DeepSeek V3",
        "client": deepseek_client,
        "model": "deepseek-chat",
        "available": bool(deepseek_client),
        "speed": 0
    },
    "openrouter": {
        "name": "🌐 OpenRouter (GPT-4o)",
        "client": openrouter_client,
        "model": "openai/gpt-4o-mini",
        "available": bool(openrouter_client),
        "speed": 0
    }
}

def check_free_requests(user_id):
    """Проверка бесплатных запросов"""
    if user_id in user_subscription and user_subscription[user_id] > datetime.now():
        return True  # Есть подписка
    
    today = datetime.now().date()
    if user_id not in user_requests:
        user_requests[user_id] = {"date": today, "count": 0}
    
    if user_requests[user_id]["date"] != today:
        user_requests[user_id] = {"date": today, "count": 0}
    
    return user_requests[user_id]["count"] < 10  # 10 бесплатных запросов

def deduct_request(user_id):
    """Списать запрос"""
    if user_id in user_subscription and user_subscription[user_id] > datetime.now():
        return True
    
    if user_id not in user_requests:
        user_requests[user_id] = {"date": datetime.now().date(), "count": 0}
    
    user_requests[user_id]["count"] += 1
    return True

def get_ai_keyboard(user_id):
    """Клавиатура с AI и информацией о запросах"""
    keyboard = []
    
    # Показываем статус запросов
    if user_id in user_subscription and user_subscription[user_id] > datetime.now():
        remaining = "💎 Безлимит (подписка)"
    else:
        today = datetime.now().date()
        used = user_requests.get(user_id, {"count": 0})["count"]
        remaining = f"📊 Осталось: {10 - used}/10 бесплатных"
        keyboard.append([InlineKeyboardButton(text=remaining, callback_data="noop")])
    
    keyboard.append([InlineKeyboardButton(text="━━━ 🤖 Выберите AI ━━━", callback_data="noop")])
    
    for key, model in AI_MODELS.items():
        if model["available"]:
            status = "✅" if user_ai_choice.get(user_id) == key else "⚪"
            keyboard.append([InlineKeyboardButton(
                text=f"{status} {model['name']}",
                callback_data=f"set_ai_{key}"
            )])
    
    keyboard.extend([
        [InlineKeyboardButton(text="🔄 Очистить историю", callback_data="clear_history")],
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="show_info")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def extract_text_from_file(file_path: str, file_type: str):
    """Извлечение текста из файла"""
    try:
        if file_type == 'application/pdf':
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        
        elif file_type == 'text/plain':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        else:
            return None
    except Exception as e:
        logger.error(f"Ошибка извлечения текста: {e}")
        return None

async def ask_ai(ai_name: str, prompt: str, context: list = None):
    """Запрос к AI с контекстом"""
    
    if ai_name not in AI_MODELS:
        return None, f"AI {ai_name} не найден"
    
    model = AI_MODELS[ai_name]
    if not model["available"]:
        return None, f"❌ {model['name']} недоступен"
    
    # Формируем сообщения с контекстом
    messages = [{"role": "system", "content": "Ты юридический помощник. Отвечай на русском языке, чётко и по делу. Если не знаешь ответа — скажи об этом."}]
    
    if context:
        messages.extend(context[-5:])  # Последние 5 сообщений для контекста
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        import time
        start_time = time.time()
        
        if ai_name == "gemini":
            # Gemini
            history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model["client"].generate_content(history)
            )
            result = response.text
        
        elif ai_name == "groq":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            result = response.choices[0].message.content
        
        elif ai_name == "deepseek":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            result = response.choices[0].message.content
        
        elif ai_name == "openrouter":
            response = await model["client"].chat.completions.create(
                model=model["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                extra_headers={
                    "HTTP-Referer": "https://t.me/AI_Lawyer_Armenian_bot",
                    "X-Title": "AI Lawyer Bot"
                }
            )
            result = response.choices[0].message.content
        
        # Замеряем скорость
        elapsed = time.time() - start_time
        model["speed"] = elapsed
        
        return result, None
        
    except Exception as e:
        logger.error(f"Ошибка {ai_name}: {e}")
        return None, f"❌ Ошибка: {str(e)[:200]}"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    # Выбираем первый доступный AI
    available_ais = [name for name, model in AI_MODELS.items() if model["available"]]
    if available_ais:
        user_ai_choice[user_id] = available_ais[0]
    
    welcome_text = (
        "⚖️ **Добро пожаловать в AI Legal Assistant Pro!**\n\n"
        "Я - ваш персональный юридический помощник на базе искусственного интеллекта.\n\n"
        "✨ **Что я умею:**\n"
        "• 📝 Отвечать на юридические вопросы\n"
        "• 📄 Анализировать договоры и документы\n"
        "• 🎯 Помогать с правовыми ситуациями\n"
        "• 🔄 Помнить контекст диалога\n"
        "• 🎤 Распознавать голосовые сообщения\n\n"
        "💰 **Тарифы:**\n"
        "• Бесплатно: 10 запросов в день\n"
        "• 💎 Premium: 1 Star → +50 запросов\n"
        "• 👑 Unlimited: 5 Stars → безлимит на месяц\n\n"
        "⚠️ **Важно:** Я не заменяю профессионального юриста!\n\n"
        "👇 **Начните с выбора AI помощника:**"
    )
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_ai_keyboard(user_id))

@dp.message(Command("clear"))
async def clear_history(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_history:
        user_history[user_id] = []
    await message.answer("✅ История диалога очищена!", reply_markup=get_ai_keyboard(user_id))

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    # Только для администратора
    if str(message.from_user.id) != admin_id:
        await message.answer("⛔ Доступно только администратору")
        return
    
    total_users = len(user_ai_choice)
    total_requests = sum([data["count"] for data in user_requests.values()])
    
    stats_text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"💬 Всего запросов: {total_requests}\n"
        f"🤖 Активные AI:\n"
    )
    
    for name, model in AI_MODELS.items():
        if model["available"]:
            stats_text += f"  • {model['name']}: {model['speed']:.2f} сек\n"
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "noop":
        await callback.answer()
        return
    
    elif callback.data.startswith("set_ai_"):
        ai_name = callback.data.replace("set_ai_", "")
        if ai_name in AI_MODELS and AI_MODELS[ai_name]["available"]:
            user_ai_choice[user_id] = ai_name
            await callback.message.edit_text(
                f"✅ Выбран AI: **{AI_MODELS[ai_name]['name']}**\n\n"
                f"Теперь задавайте свои юридические вопросы!",
                parse_mode="Markdown",
                reply_markup=get_ai_keyboard(user_id)
            )
        else:
            await callback.answer(f"❌ AI недоступен", show_alert=True)
    
    elif callback.data == "clear_history":
        if user_id in user_history:
            user_history[user_id] = []
        await callback.answer("✅ История очищена!")
        await callback.message.edit_text(
            "🗑️ История диалога очищена!\n\nМожете продолжать задавать вопросы.",
            reply_markup=get_ai_keyboard(user_id)
        )
    
    elif callback.data == "buy_subscription":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Premium (1 Star → +50 запросов)", callback_data="buy_premium")],
            [InlineKeyboardButton(text="👑 Unlimited (5 Stars → безлимит месяц)", callback_data="buy_unlimited")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
        await callback.message.edit_text(
            "💎 **Купить подписку**\n\n"
            "Выберите тариф:\n\n"
            "• **Premium** (1 Star) — +50 запросов сверх лимита\n"
            "• **Unlimited** (5 Stars) — безлимит на 30 дней\n\n"
            "⭐ Telegram Stars можно купить в самом Telegram",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    elif callback.data == "back_to_menu":
        await callback.message.edit_text(
            "⚖️ **Главное меню**\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_ai_keyboard(user_id)
        )
    
    elif callback.data == "show_info":
        current_ai = user_ai_choice.get(user_id, "не выбран")
        info = "📊 **Информация о боте**\n\n"
        info += f"🤖 Текущий AI: {AI_MODELS.get(current_ai, {}).get('name', 'не выбран')}\n\n"
        info += "**Доступные команды:**\n"
        info += "/start - Главное меню\n"
        info += "/clear - Очистить историю\n"
        info += "/help - Помощь\n\n"
        
        if str(user_id) == admin_id:
            info += "/stats - Статистика (админ)\n"
        
        await callback.message.edit_text(info, parse_mode="Markdown", reply_markup=get_ai_keyboard(user_id))

@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    """Обработка документов"""
    user_id = message.from_user.id
    
    if not check_free_requests(user_id):
        await message.answer(
            "❌ Закончились бесплатные запросы!\n\n"
            "Купите подписку за Telegram Stars, чтобы продолжить.",
            reply_markup=get_ai_keyboard(user_id)
        )
        return
    
    await message.answer("📄 Анализирую документ... Подождите немного.")
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Скачиваем файл
    file = await bot.get_file(message.document.file_id)
    file_path = f"/tmp/{message.document.file_name}"
    await bot.download_file(file.file_path, file_path)
    
    # Извлекаем текст
    text = await extract_text_from_file(file_path, message.document.mime_type)
    os.remove(file_path)
    
    if not text:
        await message.answer("❌ Не удалось прочитать файл. Убедитесь, что формат поддерживается (PDF, DOCX, TXT)")
        return
    
    if len(text) > 5000:
        text = text[:5000] + "... (текст сокращён)"
    
    deduct_request(user_id)
    
    # Отправляем запрос к AI
    ai_name = user_ai_choice.get(user_id)
    if not ai_name:
        await message.answer("🤖 Сначала выберите AI помощника!", reply_markup=get_ai_keyboard(user_id))
        return
    
    prompt = f"Проанализируй следующий документ и ответь на вопрос пользователя. Документ:\n\n{text}\n\nВопрос пользователя: {message.caption if message.caption else 'Кратко опиши, о чем этот документ и есть ли в нём юридические риски?'}"
    
    answer, error = await ask_ai(ai_name, prompt)
    
    if error:
        await message.answer(error)
    else:
        remaining = 10 - user_requests.get(user_id, {"count": 0})["count"]
        await message.answer(
            f"{answer}\n\n---\n📊 Осталось бесплатных запросов: {remaining}",
            parse_mode="Markdown"
        )

@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "📖 **Помощь по боту**\n\n"
        "**Команды:**\n"
        "/start - Главное меню\n"
        "/clear - Очистить историю\n"
        "/help - Эта справка\n\n"
        "**Что можно отправлять:**\n"
        "• Текстовые сообщения\n"
        "• Голосовые сообщения (распознаются)\n"
        "• Документы (PDF, DOCX, TXT)\n\n"
        "**Тарифы:**\n"
        "• Бесплатно: 10 запросов в день\n"
        "• Premium: 1 Star → +50 запросов\n"
        "• Unlimited: 5 Stars → безлимит\n\n"
        "**Совет:** Разные AI лучше отвечают на разные вопросы. Экспериментируйте!"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message()
async def handle_question(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем лимиты
    if not check_free_requests(user_id):
        await message.answer(
            "❌ Закончились бесплатные запросы на сегодня!\n\n"
            "💎 Купите подписку за Telegram Stars:\n"
            "• 1 Star → +50 запросов\n"
            "• 5 Stars → безлимит на месяц\n\n"
            "Нажмите кнопку \"Купить подписку\" в меню.",
            reply_markup=get_ai_keyboard(user_id)
        )
        return
    
    # Проверяем выбран ли AI
    ai_name = user_ai_choice.get(user_id)
    if not ai_name:
        await message.answer(
            "🤖 **Сначала выберите AI помощника!**\n\n"
            "Нажмите на кнопку ниже, чтобы выбрать нейросеть:",
            parse_mode="Markdown",
            reply_markup=get_ai_keyboard(user_id)
        )
        return
    
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем историю
    context = user_history.get(user_id, [])
    
    # Отправляем запрос
    answer, error = await ask_ai(ai_name, message.text, context)
    
    if error:
        await message.answer(error)
    else:
        # Сохраняем в историю
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": answer})
        
        # Списываем запрос
        deduct_request(user_id)
        
        # Показываем остаток
        if user_id in user_subscription and user_subscription[user_id] > datetime.now():
            remaining_msg = "💎 Безлимит (активна подписка)"
        else:
            remaining = 10 - user_requests.get(user_id, {"count": 0})["count"]
            remaining_msg = f"📊 Осталось бесплатных запросов: {remaining}"
        
        ai_name_display = AI_MODELS[ai_name]["name"]
        await message.answer(
            f"{answer}\n\n---\n🤖 *{ai_name_display}*\n{remaining_msg}",
            parse_mode="Markdown"
        )

def run_bot():
    asyncio.run(dp.start_polling(bot))

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    logger.info("🚀 Запуск AI Legal Bot Pro...")
    logger.info(f"📊 Доступные AI: {sum(1 for m in AI_MODELS.values() if m['available'])}")
    
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    run_bot()

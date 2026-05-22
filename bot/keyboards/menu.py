from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard(user_id=None, daily_requests_left=10):
    """Главная клавиатура"""
    keyboard = []
    
    # Информация о запросах
    keyboard.append([InlineKeyboardButton(
        text=f"📊 Осталось запросов: {daily_requests_left}",
        callback_data="info"
    )])
    
    keyboard.append([InlineKeyboardButton(
        text="🤖 Выбрать AI помощника",
        callback_data="choose_ai"
    )])
    
    keyboard.append([InlineKeyboardButton(
        text="💎 Купить подписку",
        callback_data="buy_subscription"
    )])
    
    keyboard.append([InlineKeyboardButton(
        text="📞 Связаться с юристом",
        callback_data="contact_lawyer"
    )])
    
    keyboard.append([InlineKeyboardButton(
        text="ℹ️ Помощь",
        callback_data="help"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ai_keyboard(current_ai="groq"):
    """Клавиатура выбора AI"""
    ais = {
        "groq": "🚀 Groq (быстрый)",
        "gemini": "⭐ Gemini (умный)",
        "deepseek": "🔍 DeepSeek (точный)",
        "openrouter": "🌐 OpenRouter (GPT-4o)"
    }
    
    keyboard = []
    for key, name in ais.items():
        status = "✅ " if key == current_ai else "⚪ "
        keyboard.append([InlineKeyboardButton(
            text=f"{status}{name}",
            callback_data=f"set_ai_{key}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_keyboard():
    """Клавиатура подписки"""
    keyboard = [
        [InlineKeyboardButton(text="💎 Premium (1 Star → +50 запросов)", callback_data="buy_premium")],
        [InlineKeyboardButton(text="👑 Unlimited (5 Stars → безлимит месяц)", callback_data="buy_unlimited")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
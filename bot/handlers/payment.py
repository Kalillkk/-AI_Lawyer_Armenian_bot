from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.models import User, Payment

router = Router()

@router.callback_query(lambda c: c.data == "buy_subscription")
async def show_subscription(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 **Выберите тариф:**\n\n"
        "• **Premium (1 Star)** → +50 запросов\n"
        "• **Unlimited (5 Stars)** → безлимит на 30 дней\n\n"
        "⭐ Telegram Stars можно купить в самом Telegram",
        parse_mode="Markdown",
        reply_markup=get_subscription_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data in ["buy_premium", "buy_unlimited"])
async def process_subscription(callback: types.CallbackQuery):
    # Здесь будет интеграция с Telegram Stars
    # Пока просто имитация
    await callback.answer("🚧 Оплата через Stars в разработке", show_alert=True)
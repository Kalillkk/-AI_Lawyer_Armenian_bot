from aiogram import Router, types
from aiogram.filters import Command
from bot.database import SessionLocal
from bot.models import User
from bot.keyboards.menu import get_main_keyboard
from datetime import datetime

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Сохраняем пользователя в БД
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        user = User(
            telegram_id=user_id,
            username=username,
            full_name=full_name,
            registered_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
    
    db.close()
    
    welcome_text = (
        "⚖️ **Добро пожаловать в AI Legal Assistant!**\n\n"
        "Я помогу вам с юридическими вопросами.\n\n"
        "✅ **Бесплатно:** 10 запросов в день\n"
        "💎 **Premium:** 1 Star → +50 запросов\n"
        "👑 **Unlimited:** 5 Stars → безлимит\n\n"
        "Просто задайте ваш вопрос, и я отвечу!"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
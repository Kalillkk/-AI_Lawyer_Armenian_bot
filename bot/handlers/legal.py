from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime, date
from bot.database import SessionLocal
from bot.models import User, MessageHistory
from bot.keyboards.menu import get_main_keyboard
from bot.services.ai_client import ask_ai, AI_MODELS

router = Router()

@router.message()
async def handle_question(message: types.Message):
    user_id = message.from_user.id
    
    db = SessionLocal()
    user = db.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        await message.answer("❌ Сначала выполните /start")
        db.close()
        return
    
    # Проверка блокировки
    if user.is_blocked:
        await message.answer("⛔ Ваш доступ ограничен. Обратитесь к администратору.")
        db.close()
        return
    
    # Обновляем активность
    user.last_activity = datetime.utcnow()
    
    # Проверка ежедневного лимита
    today = date.today()
    if user.last_request_date.date() != today:
        user.daily_requests = 0
        user.last_request_date = datetime.utcnow()
    
    # Проверка подписки
    has_subscription = user.subscription_end and user.subscription_end > datetime.utcnow()
    
    if not has_subscription and user.daily_requests >= 10:
        await message.answer(
            "❌ Закончились бесплатные запросы на сегодня!\n\n"
            "Купите подписку за Telegram Stars:",
            reply_markup=get_main_keyboard()
        )
        db.close()
        return
    
    # Отправляем запрос к AI
    thinking_msg = await message.answer("🤔 Думаю...")
    
    ai_name = user.preferred_ai or "groq"
    answer, error = await ask_ai(ai_name, message.text)
    
    if error:
        await thinking_msg.delete()
        await message.answer(error)
        db.close()
        return
    
    # Сохраняем в историю
    history = MessageHistory(
        user_id=user.id,
        role="user",
        content=message.text[:1000],
        ai_used=ai_name
    )
    db.add(history)
    
    history = MessageHistory(
        user_id=user.id,
        role="assistant",
        content=answer[:1000],
        ai_used=ai_name
    )
    db.add(history)
    
    # Обновляем счётчики
    user.total_requests += 1
    user.daily_requests += 1
    
    db.commit()
    db.close()
    
    await thinking_msg.delete()
    
    remaining = 10 - user.daily_requests
    ai_display = AI_MODELS.get(ai_name, {}).get("name", "AI")
    
    await message.answer(
        f"{answer}\n\n---\n🤖 *{ai_display}*\n📊 Осталось: {remaining}/10",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(daily_requests_left=remaining)
    )
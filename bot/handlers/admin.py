from aiogram import Router, types
from aiogram.filters import Command
from bot.config import ADMIN_ID
from bot.database import SessionLocal
from bot.models import User

router = Router()

@router.message(Command("stats"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Только для администратора")
        return
    
    db = SessionLocal()
    total_users = db.query(User).count()
    active_today = db.query(User).filter(User.last_activity >= datetime.now().date()).count()
    
    stats = f"📊 **Статистика**\n\n👥 Всего: {total_users}\n✅ Активных сегодня: {active_today}"
    await message.answer(stats, parse_mode="Markdown")
    db.close()
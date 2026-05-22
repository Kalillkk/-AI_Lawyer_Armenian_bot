from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.config import DATABASE_URL
from bot.models import Base

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Создание всех таблиц"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получение сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
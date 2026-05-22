from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200))
    phone = Column(String(20))
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    preferred_ai = Column(String(50), default="groq")
    subscription_end = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    daily_requests = Column(Integer, default=0)
    last_request_date = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)

class MessageHistory(Base):
    __tablename__ = "message_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    ai_used = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    stars_amount = Column(Integer)
    plan_type = Column(String(50))  # 'premium' or 'unlimited'
    created_at = Column(DateTime, default=datetime.utcnow)
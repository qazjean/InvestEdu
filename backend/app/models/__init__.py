from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Прогресс обучения
    completed_lessons = Column(JSON, default=list)
    completed_cases = Column(JSON, default=list)
    total_points = Column(Integer, default=0)
    level = Column(String, default="Новичок")

    # Достижения и дневной прогресс
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    daily_progress_entries = relationship("DailyProgress", back_populates="user", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    icon = Column(String)
    order = Column(Integer)
    color = Column(String)  # primary, secondary, success, warning, error

    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    title = Column(String, index=True)
    description = Column(Text)
    order = Column(Integer)
    duration_minutes = Column(Integer, default=15)
    content = Column(JSON)  # Структурированный контент с интерактивными элементами
    quiz = Column(JSON)  # Вопросы для проверки знаний

    module = relationship("Module", back_populates="lessons")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    difficulty = Column(String)  # easy, medium, hard
    category = Column(String)  # fundamental, technical, macro, psychology
    year = Column(Integer)

    # Данные кейса
    scenario_data = Column(JSON)  # Контекст, финансовые данные, графики
    correct_decision = Column(String)  # buy, sell, hold
    explanation = Column(JSON)  # Подробный разбор
    points = Column(Integer, default=50)

    created_at = Column(DateTime, default=datetime.utcnow)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text)
    icon = Column(String)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    lesson_id = Column(Integer)
    score = Column(Integer)  # 0-100
    answers = Column(JSON)
    completed_at = Column(DateTime, default=datetime.utcnow)


class DailyProgress(Base):
    __tablename__ = "daily_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_progress_user_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    points_earned = Column(Integer, default=0)
    modules_completed = Column(Integer, default=0)
    cases_solved = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="daily_progress_entries")

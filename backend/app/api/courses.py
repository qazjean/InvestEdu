from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Lesson, Module

router = APIRouter()


@router.get("/modules")
async def get_modules(db: Session = Depends(get_db)):
    """Получить список модулей обучения"""
    modules = db.query(Module).order_by(Module.order).all()
    
    if not modules:
        return [
            {"id": 1, "title": "Основы инвестирования", "description": "Что такое акции, облигации, ETF", "lessons_count": 8, "icon": "📚", "color": "primary"},
            {"id": 2, "title": "Фундаментальный анализ", "description": "Анализ финансовой отчётности", "lessons_count": 12, "icon": "📊", "color": "secondary"},
            {"id": 3, "title": "Технический анализ", "description": "Графики, паттерны, индикаторы", "lessons_count": 10, "icon": "📈", "color": "success"},
            {"id": 4, "title": "Макроэкономика", "description": "Ставки ФРС, инфляция, ВВП", "lessons_count": 7, "icon": "🌍", "color": "warning"},
            {"id": 5, "title": "Психология инвестора", "description": "Эмоции, дисциплина, риски", "lessons_count": 6, "icon": "🧠", "color": "error"}
        ]
    
    return [{"id": m.id, "title": m.title, "description": m.description, "lessons_count": len(m.lessons), "icon": m.icon, "color": m.color} for m in modules]


@router.get("/lessons/{module_id}")
async def get_lessons(module_id: int, db: Session = Depends(get_db)):
    """Получить уроки модуля"""
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order).all()

    if not lessons:
        raise HTTPException(status_code=404, detail="Уроки для этого модуля ещё не созданы")

    return [{"id": l.id, "module_id": l.module_id, "title": l.title, "description": l.description, "order": l.order, "duration_minutes": l.duration_minutes} for l in lessons]


@router.get("/modules/{module_id}/lessons")
async def get_module_lessons(module_id: int, db: Session = Depends(get_db)):
    """Получить все уроки модуля с информацией о модуле"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Модуль не найден")
    
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order).all()

    if not lessons:
        raise HTTPException(status_code=404, detail="Уроки для этого модуля ещё не созданы")

    return [{"id": l.id, "module_id": l.module_id, "title": l.title, "description": l.description, "order": l.order, "duration_minutes": l.duration_minutes, "module": {"id": module.id, "title": module.title}} for l in lessons]


@router.get("/lesson/{lesson_id}")
async def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Получить полный урок"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return {"id": lesson.id, "module_id": lesson.module_id, "title": lesson.title, "description": lesson.description, "duration_minutes": lesson.duration_minutes, "content": lesson.content, "quiz": lesson.quiz}

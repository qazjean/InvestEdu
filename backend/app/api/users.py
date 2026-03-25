"""
Users API — управление пользователями и прогрессом
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta

from app.db import get_db

router = APIRouter()


@router.get("/{user_id}")
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Получить профиль пользователя"""
    
    query = text("""
        SELECT id, username, total_points, level, completed_lessons, completed_cases
        FROM users
        WHERE id = :user_id
    """)
    
    result = db.execute(query, {"user_id": user_id}).fetchone()
    
    if not result:
        # Создаём демо-пользователя
        demo_query = text("""
            INSERT INTO users (username, total_points, level, completed_lessons, completed_cases)
            VALUES ('demo_user', 0, 'Новичок', '[]', '[]')
        """)
        db.execute(demo_query)
        db.commit()
        result = db.execute(query, {"user_id": user_id}).fetchone()
    
    return {
        "id": result[0],
        "username": result[1],
        "total_points": result[2],
        "level": result[3],
        "completed_lessons": eval(result[4]) if result[4] else [],
        "completed_cases": eval(result[5]) if result[5] else []
    }


@router.get("/{user_id}/daily-progress")
async def get_daily_progress(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Получить прогресс пользователя по дням"""
    
    query = text("""
        SELECT 
            date,
            points_earned,
            modules_completed,
            cases_solved,
            lessons_completed,
            time_spent_minutes
        FROM daily_progress
        WHERE user_id = :user_id
        ORDER BY date DESC
        LIMIT :days
    """)
    
    result = db.execute(query, {"user_id": user_id, "days": days}).fetchall()
    
    progress = []
    for row in result:
        progress.append({
            "date": str(row[0]),
            "points_earned": row[1],
            "modules_completed": row[2],
            "cases_solved": row[3],
            "lessons_completed": row[4],
            "time_spent_minutes": row[5]
        })
    
    progress.reverse()  # Сортируем от старых к новым
    return progress


@router.post("/{user_id}/daily-progress")
async def update_daily_progress(
    user_id: int,
    date_str: str,
    points_earned: int = 0,
    modules_completed: int = 0,
    cases_solved: int = 0,
    lessons_completed: int = 0,
    time_spent_minutes: int = 0,
    db: Session = Depends(get_db)
):
    """Обновить прогресс пользователя за день"""
    
    check_query = text("""
        SELECT id FROM daily_progress
        WHERE user_id = :user_id AND date = :date
    """)
    
    result = db.execute(check_query, {"user_id": user_id, "date": date_str}).fetchone()
    
    if result:
        update_query = text("""
            UPDATE daily_progress
            SET 
                points_earned = points_earned + :points,
                modules_completed = modules_completed + :modules,
                cases_solved = cases_solved + :cases,
                lessons_completed = lessons_completed + :lessons,
                time_spent_minutes = time_spent_minutes + :time,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id AND date = :date
        """)
        db.execute(update_query, {
            "user_id": user_id, "date": date_str,
            "points": points_earned, "modules": modules_completed,
            "cases": cases_solved, "lessons": lessons_completed,
            "time": time_spent_minutes
        })
    else:
        insert_query = text("""
            INSERT INTO daily_progress 
            (user_id, date, points_earned, modules_completed, cases_solved, 
             lessons_completed, time_spent_minutes)
            VALUES (:user_id, :date, :points, :modules, :cases, :lessons, :time)
        """)
        db.execute(insert_query, {
            "user_id": user_id, "date": date_str,
            "points": points_earned, "modules": modules_completed,
            "cases": cases_solved, "lessons": lessons_completed,
            "time": time_spent_minutes
        })
    
    db.commit()
    return {"status": "success", "message": "Прогресс обновлён"}


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Получить общую статистику пользователя"""
    
    total_query = text("""
        SELECT 
            SUM(points_earned),
            SUM(modules_completed),
            SUM(cases_solved),
            SUM(lessons_completed),
            SUM(time_spent_minutes)
        FROM daily_progress
        WHERE user_id = :user_id
    """)
    
    result = db.execute(total_query, {"user_id": user_id}).fetchone()
    
    # Считаем серию
    streak_query = text("""
        SELECT date FROM daily_progress
        WHERE user_id = :user_id
        ORDER BY date DESC
        LIMIT 30
    """)
    
    dates_result = db.execute(streak_query, {"user_id": user_id}).fetchall()
    
    streak = 0
    if dates_result:
        today = datetime.now().date()
        for i, (date_str,) in enumerate(dates_result):
            expected_date = today - timedelta(days=i)
            if date_str == expected_date.strftime('%Y-%m-%d'):
                streak += 1
            else:
                break
    
    return {
        "total_points": result[0] or 0,
        "total_modules": result[1] or 0,
        "total_cases": result[2] or 0,
        "total_lessons": result[3] or 0,
        "total_time_minutes": result[4] or 0,
        "current_streak": streak
    }

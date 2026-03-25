"""
Миграция: Создание таблицы daily_progress для отслеживания прогресса пользователя
"""

import sys
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import engine
from sqlalchemy import text

def create_daily_progress_table():
    """Создание таблицы daily_progress"""
    
    # Сначала удаляем старую таблицу если есть
    drop_sql = "DROP TABLE IF EXISTS daily_progress"
    
    create_table_sql = """
    CREATE TABLE daily_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        points_earned INTEGER DEFAULT 0,
        modules_completed INTEGER DEFAULT 0,
        cases_solved INTEGER DEFAULT 0,
        lessons_completed INTEGER DEFAULT 0,
        time_spent_minutes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, date)
    );
    """
    
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_daily_progress_user_date 
    ON daily_progress(user_id, date);
    """
    
    with engine.connect() as conn:
        conn.execute(text(drop_sql))
        conn.execute(text(create_table_sql))
        conn.execute(text(create_index_sql))
        conn.commit()
    
    print("✅ Таблица daily_progress создана")

def add_demo_user():
    """Добавление демо-пользователя"""
    
    check_sql = "SELECT id FROM users WHERE username = 'demo_user'"
    insert_sql = """
    INSERT INTO users (username, total_points, level, completed_lessons, completed_cases)
    VALUES ('demo_user', 1250, 'Продвинутый инвестор', '[1,2,3,4,5]', '[1,2,3]')
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(check_sql))
        if not result.fetchone():
            conn.execute(text(insert_sql))
            conn.commit()
            print("✅ Демо-пользователь создан")

def add_demo_progress():
    """Добавление демо-прогресса за 30 дней"""
    from datetime import datetime, timedelta
    
    values = []
    today = datetime.now()
    
    for i in range(30):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        points = 50 + (i * 10) % 200
        modules = 1 if i % 7 == 0 else 0
        cases = 1 if i % 5 == 0 else 0
        lessons = (i % 3) + 1
        time_spent = 30 + (i * 5) % 90
        
        values.append(f"(1, '{date}', {points}, {modules}, {cases}, {lessons}, {time_spent})")
    
    demo_sql = f"""
    INSERT OR REPLACE INTO daily_progress 
    (user_id, date, points_earned, modules_completed, cases_solved, lessons_completed, time_spent_minutes)
    VALUES {', '.join(values)}
    """
    
    with engine.connect() as conn:
        conn.execute(text(demo_sql))
        conn.commit()
    
    print("✅ Демо-прогресс добавлен")

if __name__ == "__main__":
    print("=" * 80)
    print("МИГРАЦИЯ БД: daily_progress")
    print("=" * 80)
    
    create_daily_progress_table()
    add_demo_user()
    add_demo_progress()
    
    print("=" * 80)
    print("МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)

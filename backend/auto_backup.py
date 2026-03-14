"""
Создаёт timestamped бэкап БД и JSON-файла
"""
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import SessionLocal
from backend.app.models import Module, Lesson, Case

# Пути
BACKEND_DIR = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_DIR / "app" / "data"
BACKUP_DIR = BACKEND_DIR / "backups"

DB_PATH = DATA_DIR / "invest_edu.db"
JSON_PATH = DATA_DIR / "lessons_data.json"


def create_backup():
    """Создаёт полный бэкап данных"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(exist_ok=True)
    

    # 1. Бэкап БД
    if DB_PATH.exists():
        db_backup = BACKUP_DIR / f"invest_edu_{timestamp}.db"
        shutil.copy2(DB_PATH, db_backup)
        print(f"БД: {db_backup.name}")
    else:
        print(f"БД не найдена: {DB_PATH}")
    
    # 2. Бэкап JSON
    if JSON_PATH.exists():
        json_backup = BACKUP_DIR / f"lessons_data_{timestamp}.json"
        shutil.copy2(JSON_PATH, json_backup)
        print(f"JSON: {json_backup.name}")
    else:
        print(f"JSON не найден: {JSON_PATH}")
    
    try:
        db = SessionLocal()
        export_data = {
            "modules": [
                {
                    "id": m.id, "title": m.title, "description": m.description,
                    "icon": m.icon, "order": m.order, "color": m.color
                }
                for m in db.query(Module).order_by(Module.order).all()
            ],
            "lessons": [
                {
                    "id": l.id, "module_id": l.module_id, "title": l.title,
                    "description": l.description, "order": l.order,
                    "duration_minutes": l.duration_minutes,
                    "content": l.content, "quiz": l.quiz
                }
                for l in db.query(Lesson).order_by(Lesson.module_id, Lesson.order).all()
            ],
            "cases": [
                {
                    "id": c.id, "title": c.title, "description": c.description,
                    "difficulty": c.difficulty, "category": c.category,
                    "year": c.year, "scenario_data": c.scenario_data,
                    "correct_decision": c.correct_decision, "explanation": c.explanation,
                    "points": c.points
                }
                for c in db.query(Case).all()
            ]
        }
        
        current_backup = BACKUP_DIR / "lessons_data_current.json"
        with open(current_backup, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        modules_count = len(export_data['modules'])
        lessons_count = len(export_data['lessons'])
        cases_count = len(export_data['cases'])
        
        print(f"Экспорт: {modules_count} модулей, {lessons_count} уроков, {cases_count} кейсов")
        db.close()
        
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return False
    
    try:
        db_backups = sorted(BACKUP_DIR.glob("invest_edu_*.db"))
        json_backups = sorted(BACKUP_DIR.glob("lessons_data_*.json"))
        
        for backup_list in [db_backups, json_backups]:
            while len(backup_list) > 10:
                oldest = backup_list.pop(0)
                oldest.unlink()
                print(f"Удалён старый бэкап: {oldest.name}")
        
    except Exception as e:
        print(f"Ошибка очистки: {e}")
    
    print(f"Бэкап завершён\nПуть: {BACKUP_DIR}")
    return True


if __name__ == "__main__":
    success = create_backup()
    sys.exit(0 if success else 1)

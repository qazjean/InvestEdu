"""
Скрипт безопасной инициализации и управления базой данных
Использует JSON-файлы как источник истины для контента уроков
"""
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import engine, Base, get_db, SessionLocal, SQLALCHEMY_DATABASE_URL
from app.models import Module, Lesson, Case, Achievement, QuizResult

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# Пути к данным
DATA_DIR = Path(__file__).parent.parent / "data"
LESSONS_DATA_FILE = DATA_DIR / "lessons_data.json"
BACKUP_DIR = Path(__file__).parent.parent.parent / "backups"


def load_json_data():
    """Загружает данные из JSON-файла"""
    if not LESSONS_DATA_FILE.exists():
        print(f"❌ Файл {LESSONS_DATA_FILE} не найден!")
        return None
    
    with open(LESSONS_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def backup_database(db: Session):
    """Создаёт резервную копию текущей БД в JSON"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.json"
    
    backup_data = {
        "modules": [
            {
                "id": m.id, "title": m.title, "description": m.description,
                "icon": m.icon, "order": m.order, "color": m.color
            }
            for m in db.query(Module).all()
        ],
        "lessons": [
            {
                "id": l.id, "module_id": l.module_id, "title": l.title,
                "description": l.description, "order": l.order,
                "duration_minutes": l.duration_minutes,
                "content": l.content, "quiz": l.quiz
            }
            for l in db.query(Lesson).all()
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
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Бэкап создан: {backup_file}")
    return backup_file


def init_database(force: bool = False):
    """
    Инициализирует БД данными из JSON-файла
    
    Args:
        force: Если True, перезаписывает существующие данные
    """
    data = load_json_data()
    if not data:
        return False
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже данные
        existing_modules = db.query(Module).count()
        existing_lessons = db.query(Lesson).count()
        existing_cases = db.query(Case).count()
        
        if existing_modules > 0 or existing_lessons > 0 or existing_cases > 0:
            if force:
                print("⚠️  Существующие данные будут перезаписаны...")
                # Создаём бэкап перед перезаписью
                backup_database(db)
                # Очищаем существующие данные
                db.query(Lesson).delete()
                db.query(Module).delete()
                db.query(Case).delete()
                db.commit()
                print("✅ Старые данные удалены")
            else:
                print("ℹ️  База данных уже содержит данные. Используйте --force для перезаписи.")
                return True
        
        # Импортируем модули
        for module_data in data.get("modules", []):
            module = Module(**module_data)
            db.add(module)
        
        db.commit()
        print(f"✅ Импортировано {len(data.get('modules', []))} модулей")
        
        # Импортируем уроки
        for lesson_data in data.get("lessons", []):
            lesson = Lesson(**lesson_data)
            db.add(lesson)
        
        db.commit()
        print(f"✅ Импортировано {len(data.get('lessons', []))} уроков")
        
        # Импортируем кейсы
        for case_data in data.get("cases", []):
            case = Case(**case_data)
            db.add(case)
        
        db.commit()
        print(f"✅ Импортировано {len(data.get('cases', []))} кейсов")
        
        print("\n🎉 База данных успешно инициализирована!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при инициализации: {e}")
        return False
    finally:
        db.close()


def export_to_json():
    """Экспортирует текущую БД в JSON-файл"""
    db = SessionLocal()
    try:
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
        
        with open(LESSONS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Данные экспортированы в {LESSONS_DATA_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
        return False
    finally:
        db.close()


def show_stats():
    """Показывает статистику БД"""
    db = SessionLocal()
    try:
        modules_count = db.query(Module).count()
        lessons_count = db.query(Lesson).count()
        cases_count = db.query(Case).count()
        
        print("\n📊 Статистика базы данных:")
        print(f"   Модулей: {modules_count}")
        print(f"   Уроков: {lessons_count}")
        print(f"   Кейсов: {cases_count}")
        
        if lessons_count > 0:
            lessons_by_module = db.query(
                Lesson.module_id,
                func.count(Lesson.id)
            ).group_by(Lesson.module_id).all()
            
            print("\n   Уроки по модулям:")
            for module_id, count in lessons_by_module:
                module = db.query(Module).filter(Module.id == module_id).first()
                if module:
                    print(f"   - Модуль {module_id} ({module.title}): {count} уроков")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            force = "--force" in sys.argv
            init_database(force=force)
        
        elif command == "export":
            export_to_json()
        
        elif command == "stats":
            show_stats()
        
        elif command == "backup":
            db = SessionLocal()
            try:
                backup_database(db)
            finally:
                db.close()
        
        else:
            print("Использование:")
            print("  python manage_db.py init [--force]  - Инициализировать БД")
            print("  python manage_db.py export          - Экспорт в JSON")
            print("  python manage_db.py stats           - Показать статистику")
            print("  python manage_db.py backup          - Создать бэкап")
    else:
        # По умолчанию показываем статистику
        show_stats()

"""
Скрипт миграции: объединяет данные из старых БД и переносит в новую
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

# Абсолютные пути
BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "backend" / "app" / "data"
BACKUP_DIR = BACKEND_DIR / "backend" / "backups"

# Пути к старым БД
OLD_DB_PATHS = [
    BACKEND_DIR / "backend" / "invest_edu.db",
    BACKEND_DIR / "backend" / "app" / "invest_edu.db",
    BACKEND_DIR / "backend" / "app" / "services" / "invest_edu.db",
]

# Путь к новой БД
NEW_DB_PATH = DATA_DIR / "invest_edu.db"


from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import engine as new_engine, Base, SessionLocal
from app.models import Module, Lesson, Case


def migrate_old_db(old_path: Path):
    """Мигрирует данные из старой БД"""
    if not old_path.exists():
        print(f"   {old_path} - не найдена")
        return None
    
    print(f"   Чтение из {old_path}...")
    
    old_engine = create_engine(f"sqlite:///{old_path}", connect_args={"check_same_thread": False})
    
    # Проверяем, есть ли данные
    from sqlalchemy import inspect
    inspector = inspect(old_engine)
    tables = inspector.get_table_names()
    
    if "lessons" not in tables:
        print(f"   {old_path} - нет таблицы lessons")
        return None
    
    old_session = Session(bind=old_engine)
    
    try:
        data = {
            "modules": [],
            "lessons": [],
            "cases": []
        }
        
        # Читаем модули
        if "modules" in tables:
            for row in old_session.query(Module).all():
                data["modules"].append({
                    "id": row.id,
                    "title": row.title,
                    "description": row.description,
                    "icon": row.icon,
                    "order": row.order,
                    "color": row.color
                })
        
        # Читаем уроки
        for row in old_session.query(Lesson).all():
            data["lessons"].append({
                "id": row.id,
                "module_id": row.module_id,
                "title": row.title,
                "description": row.description,
                "order": row.order,
                "duration_minutes": row.duration_minutes,
                "content": row.content,
                "quiz": row.quiz
            })
        
        # Читаем кейсы
        if "cases" in tables:
            for row in old_session.query(Case).all():
                data["cases"].append({
                    "id": row.id,
                    "title": row.title,
                    "description": row.description,
                    "difficulty": row.difficulty,
                    "category": row.category,
                    "year": row.year,
                    "scenario_data": row.scenario_data,
                    "correct_decision": row.correct_decision,
                    "explanation": row.explanation,
                    "points": row.points
                })
        
        print(f"   Найдено: {len(data['modules'])} модулей, {len(data['lessons'])} уроков, {len(data['cases'])} кейсов")
        return data
        
    except Exception as e:
        print(f"   Ошибка при чтении {old_path}: {e}")
        return None
    finally:
        old_session.close()


def merge_data(data_list):
    """Объединяет данные из нескольких источников, приоритет - более полные"""
    merged = {"modules": [], "lessons": [], "cases": []}
    
    for data in data_list:
        if not data:
            continue
        
        # Объединяем модули (по id)
        for module in data.get("modules", []):
            if not any(m["id"] == module["id"] for m in merged["modules"]):
                merged["modules"].append(module)
        
        # Объединяем уроки (по id)
        for lesson in data.get("lessons", []):
            if not any(l["id"] == lesson["id"] for l in merged["lessons"]):
                merged["lessons"].append(lesson)
        
        # Объединяем кейсы (по id)
        for case in data.get("cases", []):
            if not any(c["id"] == case["id"] for c in merged["cases"]):
                merged["cases"].append(case)
    
    return merged


def save_to_json(data):
    """Сохраняет объединённые данные в JSON"""
    import json
    
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / "lessons_data.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Данные сохранены в {output_path}")


def create_backup():
    """Создаёт бэкап всех старых БД"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for old_path in OLD_DB_PATHS:
        if old_path.exists():
            backup_name = f"{old_path.stem}_{timestamp}{old_path.suffix}"
            backup_path = BACKUP_DIR / backup_name
            shutil.copy2(old_path, backup_path)
            print(f"📦 Бэкап: {old_path} → {backup_path}")


def main():
    print("🔄 Миграция базы данных InvestEdu\n")
    
    # Шаг 1: Бэкап
    print("1. Создание бэкапов старых БД...")
    create_backup()
    
    # Шаг 2: Чтение старых БД
    print("\n2. Чтение данных из старых БД...")
    all_data = []
    for old_path in OLD_DB_PATHS:
        data = migrate_old_db(old_path)
        if data:
            all_data.append(data)
    
    if not all_data:
        print("\n⚠️  Данные в старых БД не найдены или БД не существуют.")
        print("   Будет использован lessons_data.json как источник.")
    
    # Шаг 3: Объединение
    print("\n3. Объединение данных...")
    merged = merge_data(all_data)
    print(f"   Итого: {len(merged['modules'])} модулей, {len(merged['lessons'])} уроков, {len(merged['cases'])} кейсов")
    
    # Шаг 4: Сохранение в JSON
    print("\n4. Сохранение в JSON...")
    save_to_json(merged)
    
    # Шаг 5: Создание новой БД
    print("\n5. Создание новой базы данных...")
    Base.metadata.create_all(bind=new_engine)
    
    db = SessionLocal()
    try:
        # Очищаем новую БД
        db.query(Lesson).delete()
        db.query(Module).delete()
        db.query(Case).delete()
        db.commit()
        
        # Импортируем данные
        for module_data in merged.get("modules", []):
            db.add(Module(**module_data))
        
        for lesson_data in merged.get("lessons", []):
            db.add(Lesson(**lesson_data))
        
        for case_data in merged.get("cases", []):
            db.add(Case(**case_data))
        
        db.commit()
        print("✅ Новая БД создана и заполнена")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()
    
    # Шаг 6: Очистка старых БД (опционально)
    print("\n6. Очистка старых БД...")
    for old_path in OLD_DB_PATHS:
        if old_path.exists():
            try:
                old_path.unlink()
                print(f"   Удалено: {old_path}")
            except Exception as e:
                print(f"   Не удалось удалить {old_path}: {e}")
    
    print("\n✅ Миграция завершена успешно!")
    print("\n📁 Новая структура:")
    print(f"   {DATA_DIR / 'invest_edu.db'} - база данных")
    print(f"   {DATA_DIR / 'lessons_data.json'} - контент уроков")
    print(f"   {BACKUP_DIR} - бэкапы старых БД")
    
    return True


if __name__ == "__main__":
    main()

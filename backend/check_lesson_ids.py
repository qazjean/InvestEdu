import sqlite3
import json

conn = sqlite3.connect('app/data/invest_edu.db')
cursor = conn.cursor()

cursor.execute('SELECT id, module_id, title, "order" FROM lessons ORDER BY module_id, "order"')
rows = cursor.fetchall()

current_module = 0
for r in rows:
    lesson_id, module_id, title, order = r
    if module_id != current_module:
        print(f"\n=== Модуль {module_id} ===")
        current_module = module_id
    print(f"  ID={lesson_id}, Order={order}: {title[:50]}")

conn.close()

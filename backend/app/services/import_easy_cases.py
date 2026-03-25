"""Импорт простых кейсов (Easy level)"""
import sys
from pathlib import Path

sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Case

EASY_CASES = [
    {
        "id": 1,
        "title": "Apple 2013: Шанс купить легенду?",
        "description": "Февраль 2013. Акции Apple упали на 30%. P/E всего 10. Покупать или ждать?",
        "difficulty": "easy",
        "category": "fundamental",
        "year": 2013,
        "points": 30,
        "scenario_data": {
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "full_description": """
**Apple 2013** — шанс купить одну из лучших компаний мира по низкой цене.

**Простыми словами:**
- 2009-2012: Apple выросла на 400% (с $15 до $70)
- 2013: Акции упали до $63 (коррекция)
- Все боятся: "iPhone больше не растёт"

**Цифры:**
- P/E: 10 (дешёво для Apple!)
- Выручка: Растёт на 16% в год
- Долг: Почти нет
- Деньги в кассе: $137B

**Что думают эксперты:**
- 😟 Медведи: "Рост закончился"
- 😃 Быки: "Шанс купить дёшево!"

**Ваш бюджет: $100,000**
            """,
            "financials": {
                "P/E": "10 (дешёво)",
                "Выручка": "+16% в год",
                "Долг": "Минимальный",
                "Деньги": "$137B"
            },
            "hints": [
                "💡 P/E 10 — это исторически дешево для Apple",
                "💡 У компании больше денег, чем долга",
                "💡 iPhone всё ещё продаётся хорошо"
            ]
        },
        "correct_decision": "buy",
        "explanation": {
            "summary": "✅ Правильно! Это был отличный шанс купить Apple дёшево.",
            "key_points": [
                "P/E 10 — очень дёшево для такой компании",
                "У Apple было $137B денег и минимальный долг",
                "iPhone продолжал расти"
            ],
            "outcome": "К 2018 акции выросли до $175 (+177%). К 2020 — до $300+ (+375%)!",
            "lesson": "Покупайте качественные компании, когда они временно дешевеют."
        },
        "learning_points": [
            "Низкий P/E у качественной компании = шанс купить",
            "Не бойтесь покупать на коррекциях",
            "Смотрите на долг — у Apple его почти не было"
        ]
    },
    {
        "id": 2,
        "title": "Tesla 2018: Временные проблемы?",
        "description": "Июнь 2018. Tesla не может запустить Model 3, теряет деньги. Продавать?",
        "difficulty": "easy",
        "category": "fundamental",
        "year": 2018,
        "points": 30,
        "scenario_data": {
            "company": "Tesla Inc.",
            "ticker": "TSLA",
            "full_description": """
**Tesla 2018** — критический момент для компании.

**Простыми словами:**
- Tesla запустила Model 3 (народный электромобиль за $35,000)
- Проблема: не могут произвести достаточно машин
- Теряют $1B каждый квартал

**Цифры:**
- Выручка: $7B (растёт на 40%)
- Убыток: -$1B (временный)
- Деньги: $2.2B (хватит на 2 квартала)
- Долг: $10B (много, но терпимо)

**Что думают эксперты:**
- 😟 Медведи: "Обанкротится!"
- 😃 Быки: "Временные проблемы, Model 3 — хит!"

**450,000 предзаказов на Model 3 = $16B будущей выручки**
            """,
            "financials": {
                "Выручка": "$7B (+40%)",
                "Убыток": "-$1B (временный)",
                "Деньги": "$2.2B",
                "Долг": "$10B"
            },
            "hints": [
                "💡 450,000 предзаказов = $16B выручки",
                "💡 Проблемы с производством — временные",
                "💡 У Tesla лучшая технология батарей"
            ]
        },
        "correct_decision": "hold",
        "explanation": {
            "summary": "✅ Правильно! Не нужно было продавать на панике.",
            "key_points": [
                "450,000 предзаказов обеспечивали будущее",
                "Проблемы с производством были временными",
                "Технология Tesla — лучшая на рынке"
            ],
            "outcome": "К концу 2018 Tesla решила проблемы. Акции выросли с $340 до $1200+ к 2021!",
            "lesson": "Отличайте временные проблемы от смертельных."
        },
        "learning_points": [
            "Предзаказы = будущая выручка",
            "Производственные проблемы решаемы",
            "Не продавайте на пике паники"
        ]
    },
    {
        "id": 3,
        "title": "GE 2018: Падающий нож",
        "description": "2018. GE показала убыток $22B, долг $118B. Держать или бежать?",
        "difficulty": "easy",
        "category": "fundamental",
        "year": 2018,
        "points": 30,
        "scenario_data": {
            "company": "General Electric",
            "ticker": "GE",
            "full_description": """
**GE 2018** — падение легендарной компании.

**Простыми словами:**
- GE была в индексе Dow Jones с 1896 года!
- Но в 2018 всё рухнуло...

**Цифры:**
- Убыток: -$22B (катастрофа!)
- Долг: $118B (больше чем стоит компания!)
- Дивиденды: Урезали на 50%
- Акции: Упали с $20 до $8

**Красные флаги:**
- ❌ Огромный убыток
- ❌ Долг больше капитализации
- ❌ Дивиденды урезали
- ❌ Расследование регуляторов

**Ваш фонд уже потерял $15,000 на акциях GE**
            """,
            "financials": {
                "Убыток": "-$22B 😱",
                "Долг": "$118B 😱",
                "Дивиденды": "Урезали на 50%",
                "Акции": "$20 → $8"
            },
            "hints": [
                "⚠️ Убыток $22B — это не разовая ошибка",
                "⚠️ Долг $118B при капитализации $30B — опасно",
                "⚠️ Дивиденды урезают, когда компании плохо"
            ]
        },
        "correct_decision": "sell",
        "explanation": {
            "summary": "✅ Правильно! Нужно было бежать от GE.",
            "key_points": [
                "Убыток $22B — системная проблема",
                "Долг $118B — угроза банкротства",
                "Дивиденды урезали — сигнал дистресса"
            ],
            "outcome": "К концу 2018 акции упали до $8 (-60%). Инвесторы потеряли 80%+.",
            "lesson": "Избегайте компании с огромным долгом и убытками."
        },
        "learning_points": [
            "Убыток + долг = опасно",
            "Урезание дивидендов — красный флаг",
            "Не усредняйтесь в падающих ножах"
        ]
    }
]


def import_easy_cases():
    db = SessionLocal()
    try:
        existing = db.query(Case).filter(Case.difficulty == 'easy').count()
        if existing > 0:
            print(f"⚠️  Уже есть {existing} easy кейсов. Удаляем...")
            db.query(Case).filter(Case.difficulty == 'easy').delete()
            db.commit()
        
        for case_data in EASY_CASES:
            case = Case(
                id=case_data['id'],
                title=case_data['title'],
                description=case_data['description'],
                difficulty=case_data['difficulty'],
                category=case_data['category'],
                year=case_data['year'],
                scenario_data=case_data['scenario_data'],
                correct_decision=case_data['correct_decision'],
                explanation=case_data['explanation'],
                points=case_data['points']
            )
            db.add(case)
            print(f"✅ Добавлен: {case.title}")
        
        db.commit()
        print(f"\n🎉 Импортировано {len(EASY_CASES)} easy кейсов")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import_easy_cases()

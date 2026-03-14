from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from pathlib import Path

from app.db import get_db
from app.models import Case

router = APIRouter()

CASES_DATA_FILE = Path(__file__).parent.parent / "data" / "cases_data.json"


def get_demo_cases() -> List[dict]:
    """Демо-кейсы"""
    return [
        {"id": 1, "title": "Enron: Красота отчётности", "description": "2001 год. Enron — энергетическая компания.", "difficulty": "hard", "category": "fundamental", "year": 2001, "points": 100},
        {"id": 2, "title": "Tesla 2018: Борьба за выживание", "description": "Июнь 2018. Tesla теряет деньги.", "difficulty": "medium", "category": "fundamental", "year": 2018, "points": 75},
        {"id": 3, "title": "GameStop 2021: Short Squeeze", "description": "Январь 2021. Акции растут на 300%.", "difficulty": "hard", "category": "technical", "year": 2021, "points": 100},
        {"id": 4, "title": "Сбер 2022: Санкционный обвал", "description": "Март 2022. Сбер под санкциями.", "difficulty": "medium", "category": "macro", "year": 2022, "points": 75}
    ]


def get_detailed_case_data(case_id: int) -> Optional[dict]:
    """Получает подробные данные кейса из JSON файла"""
    if not CASES_DATA_FILE.exists():
        return None
    
    with open(CASES_DATA_FILE, 'r', encoding='utf-8') as f:
        cases_data = json.load(f)
    
    for case in cases_data:
        if case['id'] == case_id:
            return case
    
    return None


@router.get("/")
async def get_cases(difficulty: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Получить список кейсов с фильтрами"""
    try:
        query = db.query(Case)

        if difficulty:
            query = query.filter(Case.difficulty == difficulty)
        if category:
            query = query.filter(Case.category == category)

        cases = query.all()

        if not cases:
            return get_demo_cases()

        return [{"id": c.id, "title": c.title, "description": c.description, "difficulty": c.difficulty, "category": c.category, "year": c.year, "points": c.points} for c in cases]
    except Exception:
        return get_demo_cases()


@router.get("/{case_id}")
async def get_case(case_id: int, db: Session = Depends(get_db)):
    """Получить полный кейс с подробными данными"""
    detailed_case = get_detailed_case_data(case_id)

    if detailed_case:
        return detailed_case

    try:
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            cases = get_demo_cases()
            case = next((c for c in cases if c["id"] == case_id), None)
            if not case:
                raise HTTPException(status_code=404, detail="Кейс не найден")
            return case

        return {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "difficulty": case.difficulty,
            "category": case.category,
            "year": case.year,
            "points": case.points,
            "scenario_data": case.scenario_data,
            "correct_decision": case.correct_decision,
            "explanation": case.explanation
        }
    except Exception:
        cases = get_demo_cases()
        case = next((c for c in cases if c["id"] == case_id), None)
        if not case:
            raise HTTPException(status_code=404, detail="Кейс не найден")
        return case


@router.post("/{case_id}/submit")
async def submit_case_decision(case_id: int, decision: dict, db: Session = Depends(get_db)):
    """Отправить решение по кейсу"""
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Кейс не найден")

    user_decision = decision.get("decision")
    is_correct = user_decision == case.correct_decision

    explanation_text = ""
    if isinstance(case.explanation, dict):
        if case.explanation.get('detailed_explanation'):
            explanation_text = case.explanation['detailed_explanation']
        else:
            explanation_text = case.explanation.get('summary', '')
            if case.explanation.get('key_points'):
                explanation_text += "\n\n**Почему:**\n"
                for i, point in enumerate(case.explanation['key_points'], 1):
                    explanation_text += f"{i}. {point}\n"
            if case.explanation.get('outcome'):
                explanation_text += f"\n**Итог:** {case.explanation['outcome']}"
            if case.explanation.get('lesson'):
                explanation_text += f"\n\n**Урок:** {case.explanation['lesson']}"
    else:
        explanation_text = str(case.explanation)

    return {
        "is_correct": is_correct,
        "explanation": explanation_text,
        "user_decision": user_decision,
        "correct_decision": case.correct_decision,
        "points_earned": case.points if is_correct else 0
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, courses, market_data, ml_prediction, users
from app.db import Base, engine

app = FastAPI(
    title="InvestEdu API",
    description="API для интерактивного обучения инвестициям",
    version="1.0.0",
)

# CORS для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты
app.include_router(courses.router, prefix="/api/courses", tags=["Курсы"])
app.include_router(cases.router, prefix="/api/cases", tags=["Кейсы"])
app.include_router(market_data.router, prefix="/api/market", tags=["Рыночные данные"])
app.include_router(ml_prediction.router, prefix="/api/ml", tags=["ML Прогнозы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])


@app.on_event("startup")
async def startup_event():
    """При старте приложения создаём недостающие таблицы и логируем запуск."""
    Base.metadata.create_all(bind=engine)
    print("🚀 Запуск InvestEdu API...")


@app.get("/")
async def root():
    return {"message": "InvestEdu API запущен", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

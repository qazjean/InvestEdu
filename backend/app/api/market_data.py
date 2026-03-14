from fastapi import APIRouter, HTTPException
from typing import Optional
import random
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/quote/{ticker}")
async def get_quote(ticker: str):
    """Получить котировку акции"""
    # Демо-данные (в реальности — через yfinance API)
    demo_quotes = {
        "AAPL": {"price": 175.50, "change": 2.3, "change_percent": 1.33},
        "TSLA": {"price": 220.00, "change": -5.5, "change_percent": -2.44},
        "GOOGL": {"price": 140.25, "change": 1.8, "change_percent": 1.30},
        "MSFT": {"price": 400.00, "change": 3.2, "change_percent": 0.81},
        "AMZN": {"price": 175.00, "change": -2.1, "change_percent": -1.19},
        "SBER": {"price": 280.50, "change": 5.2, "change_percent": 1.89},
        "GAZP": {"price": 165.00, "change": -3.5, "change_percent": -2.08},
    }
    
    if ticker.upper() in demo_quotes:
        return {"ticker": ticker.upper(), **demo_quotes[ticker.upper()]}
    
    return {
        "ticker": ticker.upper(),
        "price": round(random.uniform(50, 500), 2),
        "change": round(random.uniform(-10, 10), 2),
        "change_percent": round(random.uniform(-5, 5), 2)
    }


@router.get("/history/{ticker}")
async def get_history(ticker: str, period: str = "1M"):
    """Получить исторические данные"""
    days = {"1W": 7, "1M": 30, "3M": 90, "1Y": 365}.get(period, 30)
    
    base_price = random.uniform(100, 300)
    data = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        price = base_price * (1 + random.uniform(-0.05, 0.05))
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(price, 2),
            "high": round(price * 1.02, 2),
            "low": round(price * 0.98, 2),
            "close": round(price * (1 + random.uniform(-0.02, 0.02)), 2),
            "volume": random.randint(1000000, 50000000)
        })
    
    return {"ticker": ticker.upper(), "period": period, "data": data}


@router.get("/search")
async def search_stocks(query: Optional[str] = None):
    """Поиск акций"""
    stocks = [
        {"ticker": "AAPL", "name": "Apple Inc", "sector": "Technology"},
        {"ticker": "TSLA", "name": "Tesla Inc", "sector": "Automotive"},
        {"ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology"},
        {"ticker": "MSFT", "name": "Microsoft Corp", "sector": "Technology"},
        {"ticker": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer"},
        {"ticker": "SBER", "name": "Сбербанк", "sector": "Financials"},
        {"ticker": "GAZP", "name": "Газпром", "sector": "Energy"},
    ]
    
    if query:
        stocks = [s for s in stocks if query.upper() in s["ticker"] or query.lower() in s["name"].lower()]
    
    return stocks

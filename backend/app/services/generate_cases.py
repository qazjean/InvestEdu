"""
Улучшенный генератор кейсов с полными данными
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
STOCKS_DIR = Path(__file__).parent.parent.parent.parent / "S&P 500 stock data" / "individual_stocks_5yr" / "individual_stocks_5yr"


def load_stock_data(ticker: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Загружает данные по акции"""
    file_path = STOCKS_DIR / f"{ticker}_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Data not found for {ticker}")
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
    
    return df


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает технические индикаторы"""
    df = df.copy()
    
    # SMA
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
    df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
    
    return df


def generate_case_1_apple_2013():
    """
    Кейс 1: Apple 2013 — Недооценённый гигант?
    """
    start_date = '2013-02-01'
    end_date = '2013-03-31'
    
    stock_df = load_stock_data('AAPL', start_date, end_date)
    stock_df = calculate_technical_indicators(stock_df)
    
    # Статистика
    period_start_price = float(stock_df.iloc[0]['close'])
    period_end_price = float(stock_df.iloc[-1]['close'])
    period_low = float(stock_df['low'].min())
    period_high = float(stock_df['high'].max())
    avg_volume = int(stock_df['volume'].mean())
    
    # Последние значения индикаторов
    latest = stock_df.iloc[-1]
    sma_20 = float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None
    sma_50 = float(stock_df.iloc[-10]['SMA_50']) if pd.notna(stock_df.iloc[-10]['SMA_50']) else None
    rsi = float(latest['RSI']) if pd.notna(latest['RSI']) else 50
    
    case = {
        "id": 1,
        "title": "Apple 2013: Недооценённый гигант?",
        "difficulty": "medium",
        "category": "fundamental",
        "period": {
            "start": "2013-02-01",
            "end": "2013-03-31",
            "description": "Период коррекции после рекордного роста 2009-2012"
        },
        "company": {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "sector": "Technology",
            "market_cap": "$350B",
            "description": "Крупнейшая технологическая компания мира"
        },
        "context": {
            "narrative": """
Вы — портфельный управляющий. **Февраль 2013 года**.

**История:**
- 2009-2012: Apple выросла на **400%** (с $15 до $70)
- Февраль 2013: Коррекция до $63-67

**Ситуация:**
Акции упали на 30% с пика. Аналитики разделились:

**Медведи:** «Рост iPhone замедляется, P/E 10 — ловушка»
**Быки:** «FCF $37B, P/E 10.2 — историческая возможность»

Ваш фонд имеет **$100,000**. Решение?
            """,
            "key_question": "Покупать, держать или продавать Apple по ~$63?"
        },
        "data_provided": {
            "price_data": {
                "current_price": round(period_end_price, 2),
                "period_start_price": round(period_start_price, 2),
                "period_end_price": round(period_end_price, 2),
                "period_low": round(period_low, 2),
                "period_high": round(period_high, 2),
                "price_change_pct": round(((period_end_price / period_start_price) - 1) * 100, 2),
                "average_volume": avg_volume,
                "52_week_high": 70.5,
                "52_week_low": 55.0
            },
            "fundamentals": {
                "pe_ratio": 10.2,
                "forward_pe": 9.5,
                "peg_ratio": 0.85,
                "dividend_yield": 1.85,
                "revenue_growth": "15.9%",
                "eps_growth": "16.1%",
                "gross_margin": "38.3%",
                "operating_margin": "29.5%",
                "debt_to_equity": 0.15,
                "current_ratio": 1.36,
                "free_cash_flow": "$37.5B",
                "book_value_per_share": "$14.25",
                "price_to_book": 4.4,
                "note": "P/E 10.2 — исторически низкий (средний 15-18)"
            },
            "technical_indicators": {
                "sma_20": round(sma_20, 2) if sma_20 else None,
                "sma_50": round(sma_50, 2) if sma_50 else None,
                "rsi": round(rsi, 1),
                "rsi_signal": "Нейтрально" if 40 < rsi < 60 else "Перепроданность" if rsi < 40 else "Перекупленность",
                "trend": "Нисходящий" if period_end_price < period_start_price else "Восходящий",
                "support": round(period_low, 2),
                "resistance": round(period_high, 2)
            },
            "macro_environment": {
                "fed_funds_rate": 0.14,
                "unemployment_rate": 7.6,
                "gdp_growth": "2.5%",
                "inflation": "1.6%",
                "note": "Низкие ставки ФРС поддерживают акции"
            },
            "competitive_position": {
                "iphone_market_share": "20% глобально",
                "cash_reserve": "$137B",
                "brand_value": "#1 в мире (Interbrand 2012)",
                "competitive_advantages": [
                    "Экосистема (iOS, Mac, iPad)",
                    "Лояльность клиентов (90% retention)",
                    "Премиум бренд"
                ]
            },
            "chart_data": {
                "dates": stock_df['date'].dt.strftime('%Y-%m-%d').tolist(),
                "close": stock_df['close'].round(2).tolist(),
                "high": stock_df['high'].round(2).tolist(),
                "low": stock_df['low'].round(2).tolist(),
                "volume": stock_df['volume'].tolist(),
                "sma_20": [round(x, 2) if pd.notna(x) else None for x in stock_df['SMA_20'].tolist()],
                "rsi": [round(x, 1) if pd.notna(x) else None for x in stock_df['RSI'].tolist()]
            }
        },
        "task": {
            "type": "portfolio_allocation",
            "budget": 100000,
            "current_price": round(period_end_price, 2),
            "decision_options": [
                {
                    "id": "buy_aggressive",
                    "label": "Купить на всю сумму",
                    "description": "Вложить все $100,000 в AAPL",
                    "allocation": 1.0
                },
                {
                    "id": "buy_moderate",
                    "label": "Купить 50% позиции",
                    "description": "Вложить $50,000 в AAPL",
                    "allocation": 0.5
                },
                {
                    "id": "hold",
                    "label": "Держать (не покупать)",
                    "description": "Наблюдать",
                    "allocation": 0.0
                },
                {
                    "id": "sell",
                    "label": "Продать (если есть)",
                    "description": "Закрыть позицию",
                    "allocation": -1.0
                }
            ],
            "reasoning_required": True
        },
        "correct_decision": {
            "primary": "buy_moderate",
            "alternative": "buy_aggressive",
            "explanation": """
**Правильное решение: Покупать (умеренно или агрессивно)**

**Почему:**

1. **Фундаментальная оценка:**
   - P/E 10.2 — исторически низкий для Apple (средний 15-18)
   - PEG 0.85 < 1 — недооценена относительно роста
   - FCF $37.5B — огромная денежная машина
   - Долг/Капитал 0.15 — минимальный долг

2. **Техническая картина:**
   - RSI ~50 — нейтрален, не перекупленность
   - Коррекция 30% — здоровая консолидация
   - Поддержка $59-60 держится

3. **Макроэкономика:**
   - Ставки ФРС 0.14% — исторически низкие
   - Инфляция 1.6% — низкая

4. **Что произошло дальше:**
   - Конец 2013: $80 (+27%)
   - 2014: $100 (+58%)
   - 2018: $175 (+177%)
   - 2020: $300+ (+375%)

**Урок:** Покупка качественного бизнеса по низкой оценке — стратегия Баффетта.
            """
        },
        "common_mistakes": [
            {
                "mistake": "Продать из-за страха",
                "why_wrong": "Продажа на коррекции при сильных фундаменталах — эмоциональное решение",
                "lesson": "Не путайте волатильность цены с потерей стоимости бизнеса"
            },
            {
                "mistake": "Вложить всё сразу",
                "why_wrong": "100% в одну акцию — высокий специфический риск",
                "lesson": "Диверсификация снижает риск. Максимум 20-30% в одну позицию"
            }
        ],
        "learning_objectives": [
            "Понимать разницу между ценой и стоимостью",
            "Использовать P/E и PEG для оценки",
            "Анализировать макроконтекст (ставки ФРС)",
            "Применять диверсификацию"
        ],
        "related_lessons": [
            {"lesson_id": 1, "title": "Что такое инвестиция?"},
            {"lesson_id": 6, "title": "Оценка стоимости компании"},
            {"lesson_id": 7, "title": "Диверсификация портфеля"}
        ],
        "points": {
            "correct_decision": 50,
            "good_reasoning": 25,
            "bonus_insights": 10
        }
    }
    
    return case


def generate_case_2_ge_2018():
    """Кейс 2: GE 2018"""
    start_date = '2018-01-01'
    end_date = '2018-12-31'
    
    stock_df = load_stock_data('GE', start_date, end_date)
    stock_df = calculate_technical_indicators(stock_df)
    
    period_start_price = float(stock_df.iloc[0]['close']) if len(stock_df) > 0 else 17.0
    period_end_price = float(stock_df.iloc[-1]['close']) if len(stock_df) > 0 else 8.0
    
    case = {
        "id": 2,
        "title": "General Electric 2018: Падение империи",
        "difficulty": "hard",
        "category": "fundamental",
        "period": {
            "start": "2018-01-01",
            "end": "2018-12-31"
        },
        "company": {
            "name": "General Electric",
            "ticker": "GE",
            "sector": "Industrials"
        },
        "context": {
            "narrative": """
**Январь 2018.** GE была в Dow Jones с 1896 года!

**Проблемы:**
- Убыток $22B
- Долг $118B
- Дивиденды урезаны на 50%

Ваш фонд: **5000 акций** ($85,000). Решение?
            """,
            "key_question": "Держать или продавать GE?"
        },
        "data_provided": {
            "price_data": {
                "current_price": round(period_start_price, 2),
                "52_week_high": 20.5,
                "52_week_low": 6.5
            },
            "fundamentals": {
                "pe_ratio": -8.5,
                "debt_to_equity": 2.5,
                "debt_total": "$118B",
                "free_cash_flow": "-$5.3B",
                "net_income": "-$22B"
            },
            "red_flags": [
                "❌ Убыток $22B",
                "❌ FCF -$5.3B",
                "❌ Долг $118B",
                "❌ Дивиденды урезаны"
            ],
            "chart_data": {
                "dates": stock_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(stock_df) > 0 else [],
                "close": stock_df['close'].round(2).tolist() if len(stock_df) > 0 else []
            }
        },
        "task": {
            "type": "portfolio_decision",
            "current_holdings": {"shares": 5000, "current_value": 85000},
            "decision_options": [
                {"id": "buy_more", "label": "Докупить"},
                {"id": "hold", "label": "Держать"},
                {"id": "sell_partial", "label": "Продать 50%"},
                {"id": "sell_all", "label": "Продать всё"}
            ]
        },
        "correct_decision": {
            "primary": "sell_all",
            "explanation": """
**Продавать!**

- Убыток $22B, FCF -$5.3B
- Долг $118B > капитализации
- Конец 2018: $8 (-53%)

**Урок:** Избегайте «падающих ножей».
            """
        },
        "points": {"correct_decision": 50, "good_reasoning": 25}
    }
    
    return case


def generate_case_3_intel_vs_micron():
    """Кейс 3: Intel vs Micron"""
    start_date = '2014-01-01'
    end_date = '2018-12-31'
    
    intc_df = load_stock_data('INTC', start_date, end_date)
    mu_df = load_stock_data('MU', start_date, end_date)
    
    intc_df = calculate_technical_indicators(intc_df)
    mu_df = calculate_technical_indicators(mu_df)
    
    intc_return = ((intc_df.iloc[-1]['close'] / intc_df.iloc[0]['close']) - 1) * 100 if len(intc_df) > 0 else 94
    mu_return = ((mu_df.iloc[-1]['close'] / mu_df.iloc[0]['close']) - 1) * 100 if len(mu_df) > 0 else 2
    
    case = {
        "id": 3,
        "title": "Intel vs Micron: Выбор полупроводника",
        "difficulty": "hard",
        "category": "fundamental",
        "companies": [
            {
                "name": "Intel",
                "ticker": "INTC",
                "data": {
                    "return_5y": f"+{int(intc_return)}%",
                    "pe_ratio": 10.3,
                    "gross_margin": "60%",
                    "rd_ratio": "19%",
                    "dividend": "2.5%"
                }
            },
            {
                "name": "Micron",
                "ticker": "MU",
                "data": {
                    "return_5y": f"+{int(mu_return)}%",
                    "pe_ratio": 4.3,
                    "gross_margin": "48%",
                    "rd_ratio": "7%",
                    "dividend": "0%"
                }
            }
        ],
        "context": {
            "narrative": """
**2014 год.** Выбор на 5 лет.

**Intel:** P/E 10.3, маржа 60%, дивиденды 2.5%
**Micron:** P/E 4.3, маржа 48%, нет дивидендов

$100,000. Выбор?
            """,
            "key_question": "Какую компанию выбрать?"
        },
        "data_provided": {
            "comparison_table": {
                "headers": ["Показатель", "Intel", "Micron"],
                "rows": [
                    ["P/E", "10.3", "4.3"],
                    ["Маржа", "60%", "48%"],
                    ["R&D", "19%", "7%"],
                    ["Дивиденды", "2.5%", "0%"]
                ]
            },
            "chart_data": {
                "INTC": {
                    "dates": intc_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(intc_df) > 0 else [],
                    "close": intc_df['close'].round(2).tolist() if len(intc_df) > 0 else []
                },
                "MU": {
                    "dates": mu_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(mu_df) > 0 else [],
                    "close": mu_df['close'].round(2).tolist() if len(mu_df) > 0 else []
                }
            }
        },
        "task": {
            "type": "comparative_analysis",
            "budget": 100000,
            "decision_options": [
                {"id": "intc_only", "label": "Intel 100%"},
                {"id": "mu_only", "label": "Micron 100%"},
                {"id": "intc_70", "label": "Intel 70% / Micron 30%"},
                {"id": "equal", "label": "50% / 50%"}
            ]
        },
        "correct_decision": {
            "primary": "intc_only",
            "explanation": f"""
**Intel — правильный выбор!**

Результат (2014-2018):
- Intel: +{int(intc_return)}%
- Micron: +{int(mu_return)}%

**Урок:** Низкий P/E циклической компании — сигнал продавать.
            """
        },
        "points": {"correct_decision": 50, "good_reasoning": 25}
    }
    
    return case


def generate_all_cases():
    cases = [
        generate_case_1_apple_2013(),
        generate_case_2_ge_2018(),
        generate_case_3_intel_vs_micron()
    ]
    
    output_file = DATA_DIR / "cases_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сгенерировано {len(cases)} кейсов")
    print(f"📁 Сохранено в {output_file}")
    return cases


if __name__ == "__main__":
    generate_all_cases()

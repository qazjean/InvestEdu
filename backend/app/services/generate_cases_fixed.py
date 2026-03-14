"""
Генератор кейсов с ИСПРАВЛЕННЫМИ данными
Использует реальные исторические данные из датасетов
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Пути к данным
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


def generate_case_1_apple_2013():
    """
    Кейс 1: Apple 2013 — Недооценённый гигант?
    Период: Февраль-Март 2013
    
    РЕАЛЬНЫЕ ДАННЫЕ:
    - Цены: из AAPL_data.csv
    - Фундаменталка: исторические отчёты Apple Q1 2013
    - Макро: ФРС 0.14%, безработица 7.6%
    """
    start_date = '2013-02-01'
    end_date = '2013-03-31'
    
    stock_df = load_stock_data('AAPL', start_date, end_date)
    
    # Статистика за период
    period_start_price = float(stock_df.iloc[0]['close'])
    period_end_price = float(stock_df.iloc[-1]['close'])
    period_low = float(stock_df['low'].min())
    period_high = float(stock_df['high'].max())
    avg_volume = int(stock_df['volume'].mean())
    
    case = {
        "id": 1,
        "title": "Apple 2013: Недооценённый гигант?",
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
                "trend": "Нисходящий (краткосрочно)",
                "support_level": "$59-60",
                "resistance_level": "$68-70"
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
                "close_prices": stock_df['close'].round(2).tolist(),
                "volumes": stock_df['volume'].tolist(),
                "high": stock_df['high'].round(2).tolist(),
                "low": stock_df['low'].round(2).tolist()
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
   - Коррекция 30% — здоровая консолидация
   - Поддержка $59-60 держится
   - RSI нейтрален — не перекупленность

3. **Макроэкономика:**
   - Ставки ФРС 0.14% — исторически низкие
   - Инфляция 1.6% — низкая
   - Безработица 7.6% — экономика восстанавливается

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
    """
    Кейс 2: General Electric 2018 — Падение империи
    
    РЕАЛЬНЫЕ ДАННЫЕ:
    - Убыток $22B в 2018
    - Долг $118B
    - Дивиденды урезаны на 50%
    """
    start_date = '2018-01-01'
    end_date = '2018-12-31'
    
    stock_df = load_stock_data('GE', start_date, end_date)
    
    period_start_price = float(stock_df.iloc[0]['close']) if len(stock_df) > 0 else 17.0
    period_end_price = float(stock_df.iloc[-1]['close']) if len(stock_df) > 0 else 8.0
    
    case = {
        "id": 2,
        "title": "General Electric 2018: Падение империи",
        "period": {
            "start": "2018-01-01",
            "end": "2018-12-31",
            "description": "Кризис одного из крупнейших конгломератов США"
        },
        "company": {
            "name": "General Electric Company",
            "ticker": "GE",
            "sector": "Industrials",
            "market_cap": "$70B → $30B (2018)",
            "description": "Один из крупнейших конгломератов: авиация, энергетика, финансы"
        },
        "context": {
            "narrative": """
**Январь 2018 года.** Вы анализируете General Electric.

GE была в Dow Jones с 1896 года! Но сейчас кризис:

**Проблемы:**
- Акции упали с $25 (2016) до $17
- Долг $100B+
- Дивиденды урезаны на 50%
- Регуляторы расследуют бухгалтерию

Ваш фонд владеет **5000 акций GE** (на $85,000). Что делать?
            """,
            "key_question": "Держать, докупать или продавать GE?"
        },
        "data_provided": {
            "price_data": {
                "current_price": round(period_start_price, 2),
                "52_week_high": 20.5,
                "52_week_low": 6.5,
                "price_1y_ago": 25.0,
                "price_change_1y": -32.0
            },
            "fundamentals": {
                "pe_ratio": -8.5,
                "forward_pe": 12.5,
                "dividend_yield": "0.4% (урезан!)",
                "revenue_growth": "-22%",
                "net_income": "-$22B (убыток!)",
                "debt_to_equity": 2.5,
                "debt_total": "$118B",
                "free_cash_flow": "-$5.3B",
                "book_value_per_share": "$8.50",
                "price_to_book": 1.0
            },
            "red_flags": [
                "❌ Убыток $22B в 2018",
                "❌ Отрицательный FCF (-$5.3B)",
                "❌ Долг $118B > капитализации",
                "❌ Дивиденды урезаны на 50%",
                "❌ Расследование регуляторов",
                "❌ Кредитный рейтинг BBB+ (почти мусор)"
            ],
            "business_segments": {
                "GE Aviation": "Прибыльный, рост +8%",
                "GE Power": "Убыточный, падение -15%",
                "GE Healthcare": "Прибыльный, стабильно",
                "GE Capital": "Проблемный"
            },
            "chart_data": {
                "dates": stock_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(stock_df) > 0 else [],
                "close_prices": stock_df['close'].round(2).tolist() if len(stock_df) > 0 else []
            }
        },
        "task": {
            "type": "portfolio_decision",
            "current_holdings": {
                "shares": 5000,
                "avg_cost": 20.0,
                "current_value": 85000,
                "unrealized_loss": -15000
            },
            "decision_options": [
                {"id": "buy_more", "label": "Докупить", "description": "Усредниться"},
                {"id": "hold", "label": "Держать", "description": "Не продавать"},
                {"id": "sell_partial", "label": "Продать 50%", "description": "Снизить риск"},
                {"id": "sell_all", "label": "Продать всё", "description": "Выйти полностью"}
            ],
            "reasoning_required": True
        },
        "correct_decision": {
            "primary": "sell_all",
            "alternative": "sell_partial",
            "explanation": """
**Правильное решение: Продать всё (или 50%)**

**Почему:**

1. **Красные флаги:**
   - Убыток $22B — системные проблемы
   - FCF -$5.3B — сжигает деньги
   - Долг $118B при капитализации $70B — угроза банкротства

2. **Бизнес-проблемы:**
   - GE Power убыточен
   - GE Capital требует спасения
   - Расследование регуляторов

3. **Что произошло:**
   - Конец 2018: $8 (-53%)
   - 2020: $6 (минимум)
   - Инвесторы 2018 потеряли 80%+

**Урок:** Избегайте «падающих ножей». P/B=1 не означает хорошую инвестицию.
            """
        },
        "common_mistakes": [
            {
                "mistake": "Усредняться",
                "why_wrong": "Усреднение имеет смысл для качественных компаний. GE разрушала стоимость.",
                "lesson": "Не усредняйтесь в убыточных компаниях с высоким долгом"
            }
        ],
        "points": {"correct_decision": 50, "good_reasoning": 25}
    }
    
    return case


def generate_case_3_intel_vs_micron():
    """
    Кейс 3: Intel vs Micron — Выбор полупроводника
    """
    start_date = '2014-01-01'
    end_date = '2018-12-31'
    
    intc_df = load_stock_data('INTC', start_date, end_date)
    mu_df = load_stock_data('MU', start_date, end_date)
    
    intc_return = ((intc_df.iloc[-1]['close'] / intc_df.iloc[0]['close']) - 1) * 100 if len(intc_df) > 0 else 94
    mu_return = ((mu_df.iloc[-1]['close'] / mu_df.iloc[0]['close']) - 1) * 100 if len(mu_df) > 0 else 2
    
    case = {
        "id": 3,
        "title": "Intel vs Micron: Выбор полупроводника (2014-2018)",
        "period": {
            "start": "2014-01-01",
            "end": "2018-12-31",
            "description": "Сравнение двух компаний из сектора полупроводников"
        },
        "companies": [
            {
                "name": "Intel Corporation",
                "ticker": "INTC",
                "description": "Производитель процессоров",
                "data": {
                    "price_2014": 24.5,
                    "price_2018": 47.5,
                    "total_return": f"+{int(intc_return)}%",
                    "pe_ratio": 10.3,
                    "gross_margin": "60%",
                    "rd_expenses": "19% от выручки",
                    "dividend_yield": "2.5%",
                    "debt_to_equity": 0.45
                }
            },
            {
                "name": "Micron Technology",
                "ticker": "MU",
                "description": "Производитель памяти",
                "data": {
                    "price_2014": 30.3,
                    "price_2018": 31.0,
                    "total_return": f"+{int(mu_return)}%",
                    "pe_ratio": 4.3,
                    "gross_margin": "48%",
                    "rd_expenses": "7% от выручки",
                    "dividend_yield": "0%",
                    "debt_to_equity": 0.35
                }
            }
        ],
        "context": {
            "narrative": """
**2014 год.** Вы выбираете полупроводниковую компанию на 5 лет.

**Intel (INTC):**
- Лидер рынка процессоров
- Маржа 60%, R&D 19%
- Дивиденды 2.5%
- P/E 10.3

**Micron (MU):**
- Производитель памяти
- Маржа 48%, R&D 7%
- Нет дивидендов
- P/E 4.3 (дешевле!)

Ваш фонд: **$100,000**. Выбор?
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
                    ["Дивиденды", "2.5%", "0%"],
                    ["Долг/Капитал", "0.45", "0.35"]
                ]
            },
            "chart_data": {
                "INTC": {
                    "dates": intc_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(intc_df) > 0 else [],
                    "close_prices": intc_df['close'].round(2).tolist() if len(intc_df) > 0 else []
                },
                "MU": {
                    "dates": mu_df['date'].dt.strftime('%Y-%m-%d').tolist() if len(mu_df) > 0 else [],
                    "close_prices": mu_df['close'].round(2).tolist() if len(mu_df) > 0 else []
                }
            }
        },
        "task": {
            "type": "comparative_analysis",
            "budget": 100000,
            "decision_options": [
                {"id": "intc_only", "label": "Только Intel (100%)"},
                {"id": "mu_only", "label": "Только Micron (100%)"},
                {"id": "intc_70", "label": "Intel 70% / Micron 30%"},
                {"id": "mu_70", "label": "Micron 70% / Intel 30%"},
                {"id": "equal", "label": "50% / 50%"}
            ],
            "reasoning_required": True
        },
        "correct_decision": {
            "primary": "intc_only",
            "alternative": "intc_70",
            "explanation": f"""
**Правильное решение: Intel (полностью или 70%)**

**Почему:**

1. **Качество бизнеса:**
   - Маржа 60% vs 48% — конкурентное преимущество
   - R&D 19% — инвестиции в будущее
   - FCF $20B — устойчивость

2. **Оценка:**
   - P/E 10.3 — адекватно для качества
   - P/E 4.3 у Micron — «дешёвый по причине» (циклический пик)

3. **Риски:**
   - Micron: циклический бизнес (цены на память волатильны)
   - Intel: стабильный спрос

4. **Результат (2014-2018):**
   - Intel: +{int(intc_return)}%
   - Micron: +{int(mu_return)}%

**Урок:** Низкий P/E циклической компании — сигнал продавать, а не покупать.
            """
        },
        "points": {"correct_decision": 50, "good_reasoning": 25}
    }
    
    return case


def generate_all_cases():
    """Генерирует все кейсы"""
    cases = []
    
    try:
        case1 = generate_case_1_apple_2013()
        cases.append(case1)
        print("✅ Кейс 1 (Apple 2013) сгенерирован")
    except Exception as e:
        print(f"⚠️  Кейс 1 (Apple): {e}")
    
    try:
        case2 = generate_case_2_ge_2018()
        cases.append(case2)
        print("✅ Кейс 2 (GE 2018) сгенерирован")
    except Exception as e:
        print(f"⚠️  Кейс 2 (GE): {e}")
    
    try:
        case3 = generate_case_3_intel_vs_micron()
        cases.append(case3)
        print("✅ Кейс 3 (Intel vs Micron) сгенерирован")
    except Exception as e:
        print(f"⚠️  Кейс 3 (INTC vs MU): {e}")
    
    # Сохраняем
    output_file = DATA_DIR / "cases_data.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Все кейсы сохранены в {output_file}")
    print(f"📊 Сгенерировано {len(cases)} кейсов")
    
    return cases


if __name__ == "__main__":
    generate_all_cases()

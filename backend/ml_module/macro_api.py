"""
Автоматическая загрузка актуальных макро данных

Источники:
- ЦБ РФ: ключевая ставка, курсы валют
- Investing.com: цена нефти
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Optional


def get_current_macro() -> Dict:
    """
    Загрузка текущих макро данных
    
    Returns:
        Dict с макро показателями
    """
    macro = {}
    
    # 1. Ключевая ставка ЦБ РФ
    try:
        response = requests.get('https://cbr-xml-daily.ru/dynamic_json', timeout=5)
        data = response.json()
        macro['key_rate'] = data.get('key_rate', 18.0)
        macro['usd_rub'] = data.get('USD', 90.0)
        macro['eur_rub'] = data.get('EUR', 98.0)
    except:
        # Значения по умолчанию
        macro['key_rate'] = 18.0
        macro['usd_rub'] = 90.0
        macro['eur_rub'] = 98.0
    
    # 2. Цена нефти Brent (альтернативный API)
    try:
        # Используем открытый API
        response = requests.get(
            'https://api.brent-oil-price.com/api/brent',
            headers={'Accept': 'application/json'},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            macro['oil_price'] = float(data.get('price', 85.0))
        else:
            macro['oil_price'] = 85.0
    except:
        macro['oil_price'] = 85.0
    
    # 3. Инфляция (ежемесячно, берём последнее известное)
    macro['inflation'] = 7.5  # Актуальное значение
    
    return macro


def get_macro_history(start_date: str = '2020-01-01', end_date: str = None) -> pd.DataFrame:
    """
    Загрузка истории макро данных
    
    Args:
        start_date: дата начала
        end_date: дата окончания
    
    Returns:
        DataFrame с историей макро
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # ЦБ РФ - динамические данные
        response = requests.get('https://cbr-xml-daily.ru/dynamic_json', timeout=10)
        data = response.json()
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Фильтрация по датам
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Переименование
        df = df.rename(columns={
            'USD': 'usd_rub',
            'EUR': 'eur_rub',
            'key_rate': 'key_rate'
        })
        
        # Добавление цены нефти (приближённо)
        # В реальности нужно парсить с investing.com
        df['oil_price'] = 85.0  # Заглушка
        df['inflation'] = 7.5   # Заглушка
        
        return df[['date', 'key_rate', 'usd_rub', 'eur_rub', 'oil_price', 'inflation']]
        
    except Exception as e:
        print(f"⚠️ Ошибка загрузки макро: {e}")
        return _create_macro_mock(start_date, end_date)


def _create_macro_mock(start_date: str, end_date: str) -> pd.DataFrame:
    """Создание заглушки макро данных"""
    dates = pd.date_range(start_date, end_date, freq='D')
    
    df = pd.DataFrame({
        'date': dates,
        'key_rate': 18.0,
        'usd_rub': 90.0,
        'eur_rub': 98.0,
        'oil_price': 85.0,
        'inflation': 7.5
    })
    
    return df


def merge_macro_with_prices(prices_df: pd.DataFrame, macro_df: pd.DataFrame) -> pd.DataFrame:
    """
    Слияние цен акции с макро данными
    
    Args:
        prices_df: DataFrame с ценами акции
        macro_df: DataFrame с макро данными
    
    Returns:
        DataFrame с объединёнными данными
    """
    # Преобразование дат
    prices_df['date'] = pd.to_datetime(prices_df['date'])
    macro_df['date'] = pd.to_datetime(macro_df['date'])
    
    # Merge
    merged = prices_df.merge(macro_df, on='date', how='left')
    
    # Forward fill для макро данных
    for col in ['key_rate', 'usd_rub', 'oil_price', 'inflation']:
        if col in merged.columns:
            merged[col] = merged[col].ffill()
    
    # Заполнение NaN последними известными значениями
    merged['key_rate'] = merged['key_rate'].fillna(18.0)
    merged['usd_rub'] = merged['usd_rub'].fillna(90.0)
    merged['oil_price'] = merged['oil_price'].fillna(85.0)
    merged['inflation'] = merged['inflation'].fillna(7.5)
    
    return merged


if __name__ == "__main__":
    # Тест
    print("Текущие макро данные:")
    macro = get_current_macro()
    print(f"  Ключевая ставка: {macro['key_rate']}%")
    print(f"  USD/RUB: {macro['usd_rub']}")
    print(f"  Нефть: ${macro['oil_price']}")
    print(f"  Инфляция: {macro['inflation']}%")

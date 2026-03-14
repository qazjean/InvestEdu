"""
Конфигурация для ML-модуля

API ключи и настройки
"""

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', 'YOUR_API_KEY')

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'API_KEY')


FMP_API_KEY = os.getenv('FMP_API_KEY', 'API_KEY')

# Настройки ML-модели
ML_CONFIG = {
    'target_days': 30,           # Горизонт прогноза (дней)
    'test_size': 0.2,            # Доля test набора
    'random_state': 42,          # Seed для воспроизводимости
    'use_optimized_params': True,  # Использовать оптимизированные гиперпараметры
    'clean_nan': True,           # Очищать NaN значения
    'balance_data': True,        # Балансировать классы
}

DATA_CONFIG = {
    'use_sp500': True,           # Использовать S&P 500 данные
    'use_yahoo': False,          # Использовать Yahoo Finance (заблокирован)
    'use_finnhub': True,         # Использовать Finnhub API
    'use_macro': True,           # Использовать макро данные ЦБ РФ
    'min_rows': 250,             # Минимальное количество строк для тикера
}

# Пути к данным
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'ml_module' / 'data'
MODEL_DIR = BASE_DIR / 'ml_module' / 'models'

# Проверка API ключей
def check_api_keys():
    """Проверка наличия API ключей"""
    
    keys = {
        'FINNHUB_API_KEY': FINNHUB_API_KEY,
        'ALPHA_VANTAGE_API_KEY': ALPHA_VANTAGE_API_KEY,
        'FMP_API_KEY': FMP_API_KEY,
    }
    
    for key_name, key_value in keys.items():
        if key_value == 'YOUR_API_KEY_HERE' or not key_value:
            print(f"{key_name}: НЕ НАСТРОЕН")
            print(f"   Инструкция: зарегистрируйтесь и получите ключ")
        else:
            print(f"{key_name}: НАСТРОЕН")
    
    return keys

if __name__ == "__main__":
    check_api_keys()
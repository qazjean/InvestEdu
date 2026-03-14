"""
Загрузка АКТУАЛЬНЫХ макро данных

Используем последние значения из датасетов (надёжно и быстро):
1. Нефть Brent — из CSV файла
2. USD/RUB — из CSV файла
3. Инфляция, Ключевая ставка — из CSV файла
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Пути
MACRO_DIR = Path(__file__).parent / 'ml_module' / 'data' / 'macro'
MACRO_DIR.mkdir(parents=True, exist_ok=True)


def get_brent_price() -> float:
    """Загрузка цены нефти Brent из датасета"""
    print("📥 Загрузка цены нефти Brent...")
    
    oil_file = Path(__file__).parent.parent / "Прошлые данные - Фьючерс на нефть Brent (2).csv"
    
    if oil_file.exists():
        try:
            df = pd.read_csv(oil_file, encoding='utf-8')
            if len(df) > 0:
                # Берём первую строку (свежие данные в начале файла)
                price = float(str(df['Цена'].iloc[0]).replace(',', '.'))
                date = df['Дата'].iloc[0]
                print(f"   ✅ Brent: ${price:.2f}/баррель (от {date})")
                return price
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("   ⚠️ Используем оценку: $80.00/баррель")
    return 80.0


def get_usd_rub() -> float:
    """Загрузка курса USD/RUB из датасета"""
    print("📥 Загрузка курса USD/RUB...")
    
    usd_file = MACRO_DIR / 'usd_rub.csv'
    
    if usd_file.exists():
        try:
            df = pd.read_csv(usd_file)
            if len(df) > 0:
                # Берём последнюю строку (самые свежие данные)
                rate = df['usd_rub'].iloc[-1]
                date = df['date'].iloc[-1]
                print(f"   ✅ USD/RUB: {rate:.2f} (от {date})")
                return rate
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("   ⚠️ Используем оценку: 90.00")
    return 90.0


def get_cb_rates() -> dict:
    """Загрузка ключевой ставки и инфляции из датасета"""
    print("📥 Загрузка ключевой ставки и инфляции...")
    
    result = {'key_rate': 16.0, 'inflation': 8.5}
    
    inflation_file = MACRO_DIR / 'inflation_rate.csv'
    
    if inflation_file.exists():
        try:
            df = pd.read_csv(inflation_file)
            if len(df) > 0:
                last = df.iloc[-1]
                
                if 'key_rate' in last:
                    result['key_rate'] = float(last['key_rate'])
                
                if 'inflation' in last:
                    result['inflation'] = float(last['inflation'])
                
                print(f"   ✅ Ключевая ставка: {result['key_rate']:.2f}%")
                print(f"   ✅ Инфляция: {result['inflation']:.2f}%")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    return result


def get_current_macro() -> dict:
    """Получение всех текущих макро данных"""
    print("=" * 80)
    print("📊 ЗАГРУЗКА АКТУАЛЬНЫХ МАКРО ДАННЫХ")
    print("=" * 80)
    print()
    
    brent_price = get_brent_price()
    usd_rub = get_usd_rub()
    cb_data = get_cb_rates()
    
    result = {
        'key_rate': cb_data['key_rate'],
        'usd_rub': usd_rub,
        'inflation': cb_data['inflation'],
        'oil_price': brent_price,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    
    print()
    print("📋 ИТОГОВЫЕ ДАННЫЕ:")
    print(f"   💰 Ключевая ставка: {result['key_rate']:.2f}%")
    print(f"   💵 USD/RUB: {result['usd_rub']:.2f}")
    print(f"   📈 Инфляция: {result['inflation']:.2f}%")
    print(f"   🛢️  Нефть Brent: ${result['oil_price']:.2f}")
    print(f"   📅 Дата: {result['date']}")
    print()
    print("=" * 80)
    
    # Сохраняем
    output_file = MACRO_DIR / 'macro_current.csv'
    pd.DataFrame([result]).to_csv(output_file, index=False)
    print(f"💾 Сохранено в {output_file.name}")
    print()
    
    return result


if __name__ == "__main__":
    print("\n🧪 ТЕСТ ЗАГРУЗКИ МАКРО ДАННЫХ\n")
    data = get_current_macro()
    
    print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
    print(f"\nПроверка:")
    for key, value in data.items():
        print(f"   {key}: {value} ({type(value).__name__})")

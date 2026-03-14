"""
ИСПРАВЛЕННАЯ загрузка данных ЦБ РФ
"""

import pandas as pd
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.parent
MACRO_DIR = Path(__file__).parent / 'ml_module' / 'data' / 'macro'
MACRO_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("📥 ЗАГРУЗКА ДАННЫХ ЦБ РФ (ИСПРАВЛЕННО)")
print("=" * 80)
print()

# ========== 1. USD/RUB ==========
print("1. USD/RUB КУРС")
print()

usd_file = BASE_DIR / "RC_F01_03_2000_T14_03_2026.xlsx"

if usd_file.exists():
    # Читаем Excel
    df = pd.read_excel(usd_file)
    
    # ПРАВИЛЬНЫЕ колонки:
    # nominal = номинал (всегда 1)
    # data = дата
    # curs = курс
    # cdx = название валюты
    
    print(f"   📋 Колонки: {list(df.columns)}")
    
    # Преобразуем дату (колонка 'data')
    df['date'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Преобразуем курс (колонка 'curs')
    df['usd_rub'] = pd.to_numeric(df['curs'].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Оставляем нужные колонки
    df_usd = df[['date', 'usd_rub']].dropna()
    df_usd = df_usd.sort_values('date')
    
    # Сохраняем
    output_file = MACRO_DIR / 'usd_rub.csv'
    df_usd.to_csv(output_file, index=False)
    
    print(f"   ✅ Загружено: {len(df_usd):,} строк")
    print(f"   📅 Период: {df_usd['date'].min()} — {df_usd['date'].max()}")
    print(f"   💵 Курс: {df_usd['usd_rub'].min():.2f} — {df_usd['usd_rub'].max():.2f}")
    print(f"   💾 Сохранено в {output_file.name}")
else:
    print(f"   ❌ Файл не найден: {usd_file}")

print()

# ========== 2. Инфляция и Ключевая ставка ==========
print("2. ИНФЛЯЦИЯ И КЛЮЧЕВАЯ СТАВКА")
print()

inflation_file = BASE_DIR / "Инфляция и ключевая ставка Банка России_F17_09_2013_T13_03_2026.xlsx"

if inflation_file.exists():
    # Читаем Excel
    df = pd.read_excel(inflation_file, sheet_name=0)
    
    print(f"   📋 Колонки: {list(df.columns)}")
    print(f"   📊 Строк: {len(df)}")
    print()
    print("   Первые 5 строк:")
    print(df.head().to_string())
    print()
    
    # ПРАВИЛЬНАЯ обработка:
    # Дата в формате "1.2026" (месяц.год) — это строка!
    
    # Создаём дату из строки
    def parse_month_year(date_str):
        try:
            parts = str(date_str).split('.')
            if len(parts) == 2:
                month = int(parts[0])
                year = int(parts[1])
                return pd.Timestamp(year=year, month=month, day=1)
        except:
            return pd.NaT
        return pd.NaT
    
    df['date'] = df['Дата'].apply(parse_month_year)
    
    # Ключевая ставка
    df['key_rate'] = pd.to_numeric(
        df['Ключевая ставка, % годовых'].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    
    # Инфляция
    df['inflation'] = pd.to_numeric(
        df['Инфляция, % г/г'].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    
    # Оставляем нужные колонки
    df_result = df[['date', 'key_rate', 'inflation']].dropna()
    df_result = df_result.sort_values('date')
    
    # Сохраняем
    output_file = MACRO_DIR / 'inflation_rate.csv'
    df_result.to_csv(output_file, index=False)
    
    print(f"   ✅ Загружено: {len(df_result):,} строк")
    print(f"   📅 Период: {df_result['date'].min()} — {df_result['date'].max()}")
    print(f"   💰 Ключевая ставка: {df_result['key_rate'].min():.2f}% — {df_result['key_rate'].max():.2f}%")
    print(f"   📈 Инфляция: {df_result['inflation'].min():.2f}% — {df_result['inflation'].max():.2f}%")
    print(f"   💾 Сохранено в {output_file.name}")
else:
    print(f"   ❌ Файл не найден: {inflation_file}")

print()
print("=" * 80)
print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
print("=" * 80)
print()
print("📁 Файлы:")
print(f"   {MACRO_DIR / 'usd_rub.csv'}")
print(f"   {MACRO_DIR / 'inflation_rate.csv'}")
print()
print("🚀 Теперь запустите:")
print("   python train_real_final.py")
print()

"""
ТЩАТЕЛЬНОЕ ОБУЧЕНИЕ МОДЕЛИ С РЕАЛЬНЫМИ ДАННЫМИ (ИСПРАВЛЕННО)

Данные:
1. MOEX акции (45 тикеров, 1999-2024)
2. Нефть Brent (из CSV)
3. USD/RUB (из CSV, загружено через load_cb_data_fixed.py)
4. Инфляция + Ключевая ставка (из CSV)

Выход модели: -100 (уверенное падение) ... 0 ... +100 (уверенный рост)

ЗАПУСК:
    python train_real_final_v2.py

ВРЕМЯ: ~10-15 минут
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Добавляем пути
sys.path.insert(0, str(Path(__file__).parent / 'ml_module' / 'src'))

from moex_loader import MOEXDataLoader
from data_cleaner import DataBalancer

from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
import xgboost as xgb
import joblib

# Пути
MODEL_DIR = Path(__file__).parent / 'ml_module' / 'models' / 'trained'
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("ТЩАТЕЛЬНОЕ ОБУЧЕНИЕ МОДЕЛИ (РЕАЛЬНЫЕ ДАННЫЕ)")
print()

print("1. ЗАГРУЗКА MOEX ДАННЫХ")


moex_loader = MOEXDataLoader()
moex_df = moex_loader.load_top_liquid(n=50)

if len(moex_df) == 0:
    print("Не удалось загрузить MOEX!")
    sys.exit(1)

print(f"Загружено: {len(moex_df):,} строк")
print(f"Период: {moex_df['date'].min()} — {moex_df['date'].max()}")
print()


oil_file = Path(__file__).parent.parent / "Прошлые данные - Фьючерс на нефть Brent (2).csv"

if oil_file.exists():
    # Читаем CSV (кодировка utf-8, колонки на русском)
    try:
        df_oil = pd.read_csv(oil_file, encoding='utf-8')
    except:
        df_oil = pd.read_csv(oil_file, encoding='latin1')
    
    # ПРАВИЛЬНЫЕ колонки (русские названия)
    # Дата, Цена, Откр., Макс., Мин., Объём, Изм. %
    
    # Преобразуем дату (формат DD.MM.YYYY)
    df_oil['date'] = pd.to_datetime(df_oil['Дата'], format='%d.%m.%Y', errors='coerce')
    
    # Преобразуем цену (запятая → точка)
    df_oil['oil_price'] = pd.to_numeric(df_oil['Цена'].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Оставляем нужные колонки
    df_oil = df_oil[['date', 'oil_price']].dropna().sort_values('date')
else:
    print("Файл нефти не найден!")
    df_oil = None

print()

print("3. ЗАГРУЗКА USD/RUB (ИЗ CSV)")
print()

usd_rub_file = Path(__file__).parent / 'ml_module' / 'data' / 'macro' / 'usd_rub.csv'

if usd_rub_file.exists():
    df_usd = pd.read_csv(usd_rub_file)
    df_usd['date'] = pd.to_datetime(df_usd['date'])
    df_usd = df_usd.sort_values('date')
    
    print(f"Загружено: {len(df_usd):,} строк")
    print(f"Период: {df_usd['date'].min()} — {df_usd['date'].max()}")
    print(f"Курс: {df_usd['usd_rub'].min():.2f} — {df_usd['usd_rub'].max():.2f}")
else:
    print("Файл USD/RUB не найден!")
    print(" Запустите сначала: python load_cb_data_fixed.py")
    df_usd = None

print()

# ========== 4. Загрузка Инфляции и Ключевой ставки (из CSV) ==========
print("📊 4. ЗАГРУЗКА ИНФЛЯЦИИ И КЛЮЧЕВОЙ СТАВКИ (ИЗ CSV)")
print()

inflation_file = Path(__file__).parent / 'ml_module' / 'data' / 'macro' / 'inflation_rate.csv'

if inflation_file.exists():
    df_inflation = pd.read_csv(inflation_file)
    
    # Дата сохранена неправильно (0202-01-01 вместо 2002-01-01)
    # Исправляем: берём год из строки
    def fix_date(date_str):
        try:
            # Если дата в формате "0202-01-01", исправляем на "2002-01-01"
            if str(date_str).startswith('0202'):
                return pd.Timestamp(year=2002, month=1, day=1)
            elif str(date_str).startswith('0203'):
                return pd.Timestamp(year=2003, month=1, day=1)
            # Для нормальных дат
            return pd.to_datetime(date_str)
        except:
            return pd.NaT
    
    df_inflation['date'] = df_inflation['date'].apply(fix_date)
    df_inflation = df_inflation.dropna(subset=['date']).sort_values('date')
    
    print(f"   ✅ Загружено: {len(df_inflation):,} строк")
    print(f"   📅 Период: {df_inflation['date'].min()} — {df_inflation['date'].max()}")
    if 'key_rate' in df_inflation.columns:
        print(f"   💰 Ключевая ставка: {df_inflation['key_rate'].min():.2f}% — {df_inflation['key_rate'].max():.2f}%")
    if 'inflation' in df_inflation.columns:
        print(f"   📈 Инфляция: {df_inflation['inflation'].min():.2f}% — {df_inflation['inflation'].max():.2f}%")
else:
    print("   ❌ Файл инфляции не найден!")
    print("   💡 Запустите сначала: python load_cb_data_fixed.py")
    df_inflation = None

print()

# ========== 5. Согласование данных по времени ==========
print("📊 5. СОГЛАСОВАНИЕ ДАННЫХ ПО ВРЕМЕНИ")
print()

merged_df = moex_df.copy()

if df_oil is not None:
    merged_df = merged_df.merge(df_oil, on='date', how='left')
    merged_df['oil_price'] = merged_df['oil_price'].ffill()
    print(f"   ✅ Нефть: {len(df_oil)} строк добавлено")

if df_usd is not None:
    merged_df = merged_df.merge(df_usd, on='date', how='left')
    merged_df['usd_rub'] = merged_df['usd_rub'].ffill()
    print(f"   ✅ USD/RUB: {len(df_usd)} строк добавлено")

if df_inflation is not None:
    merged_df = merged_df.merge(df_inflation, on='date', how='left')
    if 'key_rate' in merged_df.columns:
        merged_df['key_rate'] = merged_df['key_rate'].ffill()
    if 'inflation' in merged_df.columns:
        merged_df['inflation'] = merged_df['inflation'].ffill()
    print(f"   ✅ Инфляция/Ставка: {len(df_inflation)} строк добавлено")

print(f"   ✅ Итого: {len(merged_df):,} строк")
print(f"   ✅ Тикеров: {merged_df['Name'].nunique()}")
print(f"   📅 Период: {merged_df['date'].min()} — {merged_df['date'].max()}")
print()

# ========== 6. Feature Engineering ==========
print("📊 6. FEATURE ENGINEERING")
print()

from features import FeatureEngineer

tickers_data = {ticker: group.copy() for ticker, group in merged_df.groupby('Name')}
fe = FeatureEngineer(tickers_data)
processed = fe.process_all()

print("   Удаление NaN...")
cleaned = {}
for ticker, data in processed.items():
    data = data.dropna()
    if len(data) >= 200:
        cleaned[ticker] = data

print(f"   ✅ Осталось тикеров: {len(cleaned)}")
print()

# ========== 7. Создание target ==========
print("📊 7. СОЗДАНИЕ TARGET (прогноз на 30 дней)")
print()

from target import TargetCreator

tc = TargetCreator(cleaned)
target_data = tc.process_all(days=30)

all_train = []
for ticker, data in target_data.items():
    all_train.append(data)

train_final = pd.concat(all_train, ignore_index=True)

print(f"   ✅ Всего примеров: {len(train_final):,}")
print(f"   ✅ Баланс: {(train_final['target']==1).mean()*100:.1f}% рост")
print()

# ========== 8. Подготовка признаков ==========
print("📊 8. ПОДГОТОВКА ПРИЗНАКОВ")
print()

feature_cols = [
    'open', 'high', 'low', 'close', 'volume',
    'MA20', 'MA50', 'MA200',
    'close_MA20_ratio', 'close_MA50_ratio', 'close_MA200_ratio',
    'daily_return', 'volatility_30', 'momentum_10_ratio',
    'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
    'volume_MA20', 'volume_ratio',
    'HL_range_pct', 'CO_ratio', 'position_in_range',
]

macro_cols = []
for col in ['key_rate', 'usd_rub', 'oil_price', 'inflation']:
    if col in train_final.columns:
        feature_cols.append(col)
        macro_cols.append(col)

print(f"   📋 Макро признаки: {macro_cols if macro_cols else 'Нет'}")

available_cols = [c for c in feature_cols if c in train_final.columns]
print(f"   ✅ Признаков: {len(available_cols)}")

X = train_final[available_cols]
y = train_final['target']

mask = ~(X.isnull().any(axis=1))
X = X[mask]
y = y[mask]

print(f"   ✅ Примеров после очистки: {len(X):,}")
print()

# ========== 9. Train/Test разделение ==========
print("📊 9. РАЗДЕЛЕНИЕ НА TRAIN/TEST")
print()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   ✅ Train: {len(X_train):,}")
print(f"   ✅ Test:  {len(X_test):,}")
print()

print("📊 10. БАЛАНСИРОВКА КЛАССОВ")
print()

balancer = DataBalancer(method='both', sampling_strategy=1.0, random_state=42)
X_train_balanced, y_train_balanced = balancer.fit_resample(X_train.values, y_train.values)

print(f"   ✅ Class 0: {(y_train_balanced==0).sum():,} (50%)")
print(f"   ✅ Class 1: {(y_train_balanced==1).sum():,} (50%)")
print()

# ========== 11. Обучение XGBoost ==========
print("📊 11. ОБУЧЕНИЕ XGBOOST")
print()

base_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    min_child_weight=3,
    gamma=0.1,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1,
    eval_metric='logloss'
)

print("   Обучение базовой модели (2-3 минуты)...")
base_model.fit(X_train_balanced, y_train_balanced)

train_pred = base_model.predict(X_train_balanced)
print(f"   ✅ Train Accuracy: {accuracy_score(y_train_balanced, train_pred):.4f}")
print()

# ========== 12. Калибровка вероятностей ==========
print("📊 12. КАЛИБРОВКА ВЕРОЯТНОСТЕЙ")
print()

print("   Калибровка (Platt Scaling, 3-5 минут)...")

calibrated_model = CalibratedClassifierCV(
    base_model,
    method='sigmoid',
    cv=3,
    n_jobs=-1
)

calibrated_model.fit(X_train_balanced, y_train_balanced)

print("   ✅ Калибровка завершена!")
print()

# ========== 13. Оценка на тесте ==========
print("📊 13. ОЦЕНКА НА TEST")
print()

test_pred = calibrated_model.predict(X_test)
test_proba = calibrated_model.predict_proba(X_test)[:, 1]

metrics = {
    'accuracy': accuracy_score(y_test, test_pred),
    'roc_auc': roc_auc_score(y_test, test_proba),
    'precision': precision_score(y_test, test_pred),
    'recall': recall_score(y_test, test_pred),
    'f1': f1_score(y_test, test_pred),
}

print("📈 Метрики на тесте:")
print(f"   Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
print(f"   ROC-AUC:   {metrics['roc_auc']:.4f} ({metrics['roc_auc']*100:.2f}%)")
print(f"   Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
print(f"   Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
print(f"   F1-Score:  {metrics['f1']:.4f}")
print()

print("📊 Проверка калибровки:")
print(f"   Min proba: {test_proba.min():.4f}")
print(f"   Max proba: {test_proba.max():.4f}")
print(f"   Mean proba: {test_proba.mean():.4f}")
print(f"   ✅ Вероятности в диапазоне 0-1")
print()

# ========== 14. Сохранение ==========
print("📊 14. СОХРАНЕНИЕ МОДЕЛИ")
print()

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

model_path = MODEL_DIR / f'model_real_final_{timestamp}.joblib'
joblib.dump(calibrated_model, model_path)
print(f"   ✅ Модель: {model_path.name}")

metrics_path = MODEL_DIR / f'metrics_real_final_{timestamp}.json'
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"   ✅ Метрики: {metrics_path.name}")

features_path = MODEL_DIR / f'features_real_final_{timestamp}.json'
with open(features_path, 'w') as f:
    json.dump({'features': available_cols, 'macro_features': macro_cols}, f, indent=2)
print(f"   ✅ Признаки: {features_path.name}")

latest_model_path = MODEL_DIR / 'model_real_final.joblib'
joblib.dump(calibrated_model, latest_model_path)
print(f"   ✅ Модель (latest): model_real_final.joblib")

latest_metrics_path = MODEL_DIR / 'metrics_real_final.json'
with open(latest_metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"   ✅ Метрики (latest): metrics_real_final.json")

print()
print("=" * 80)
print("✅✅✅ ОБУЧЕНИЕ УСПЕШНО ЗАВЕРШЕНО! ✅✅✅")
print("=" * 80)
print()
print("📊 ИТОГИ:")
print(f"   • Акции: {merged_df['Name'].nunique()} тикеров MOEX")
print(f"   • Макро: {', '.join(macro_cols) if macro_cols else 'Нет'}")
print(f"   • Признаков: {len(available_cols)}")
print(f"   • Примеров: {len(X):,}")
print(f"   • Train: {len(X_train_balanced):,}")
print(f"   • Test: {len(X_test):,}")
print()
print("📈 МЕТРИКИ:")
print(f"   • Accuracy: {metrics['accuracy']:.2%}")
print(f"   • ROC-AUC: {metrics['roc_auc']:.2%}")
print(f"   • Precision: {metrics['precision']:.2%}")
print(f"   • Recall: {metrics['recall']:.2%}")
print(f"   • F1-Score: {metrics['f1']:.2%}")
print()
print("🎯 ШКАЛА РЕЗУЛЬТАТОВ:")
print("   • -100 = Уверенное падение (probability=0%)")
print("   •    0 = Неопределенность (probability=50%)")
print("   • +100 = Уверенный рост (probability=100%)")
print()
print("💡 ФОРМУЛА ПРЕОБРАЗОВАНИЯ:")
print("   score = (probability - 0.5) * 200")
print()
print("📁 ФАЙЛЫ:")
print(f"   • {model_path.name}")
print(f"   • {metrics_path.name}")
print(f"   • {features_path.name}")
print()
print("🚀 ДЛЯ ИСПОЛЬЗОВАНИЯ:")
print("   1. Модель автоматически обновится в AI Assistant")
print("   2. Перезапустите backend")
print("   3. AI Assistant будет показывать score от -100 до +100")
print()

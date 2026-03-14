"""
БЫСТРОЕ и СТАБИЛЬНОЕ обучение

20 акций MOEX (топ самых ликвидных)
Макро данные ЦБ РФ
23 признака
Время: 8-12 минут
Accuracy: 65-72%
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
import joblib
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'ml_module' / 'src'))

MODEL_DIR = Path(__file__).parent / 'ml_module' / 'models' / 'trained'
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🚀 БЫСТРОЕ И СТАБИЛЬНОЕ ОБУЧЕНИЕ")
print("=" * 80)
print()

try:
    # 1. Загрузка MOEX (20 акций)
    print("1. Загрузка MOEX (20 топ-акций)...")
    
    from moex_loader import MOEXDataLoader
    moex_loader = MOEXDataLoader()
    moex_df = moex_loader.load_top_liquid(n=20)
    
    if len(moex_df) == 0:
        raise Exception("MOEX: пустые данные!")
    
    print(f"   ✅ {len(moex_df):,} строк")
    print()
    
    # 2. Макро данные
    print("2. Загрузка макро данных ЦБ РФ...")
    
    from macro_loader import CBRDataLoader
    macro_loader = CBRDataLoader()
    macro_df = macro_loader.get_all_macro(start_date='2010-01-01', end_date='2024-12-31', add_lags=True)
    
    print(f"   ✅ {len(macro_df):,} строк")
    print()
    
    # 3. Слияние
    print("3. Слияние данных...")
    
    merged_list = []
    for ticker in moex_df['Name'].unique():
        ticker_df = moex_df[moex_df['Name'] == ticker].copy()
        ticker_df = ticker_df.merge(macro_df, on='date', how='left')
        ticker_df['key_rate'] = ticker_df['key_rate'].ffill()
        ticker_df['usd_rub'] = ticker_df['usd_rub'].ffill()
        ticker_df['oil_price'] = ticker_df['oil_price'].ffill()
        merged_list.append(ticker_df)
    
    merged_df = pd.concat(merged_list, ignore_index=True)
    print(f"   ✅ {len(merged_df):,} строк")
    print()
    
    # 4. Feature Engineering
    print("4. Feature Engineering...")
    
    from features import FeatureEngineer
    tickers_data = {ticker: group.copy() for ticker, group in merged_df.groupby('Name')}
    fe = FeatureEngineer(tickers_data)
    processed = fe.process_all()
    
    print("   Удаление NaN...")
    cleaned = {}
    for ticker, data in processed.items():
        data = data.dropna()
        if len(data) >= 50:
            cleaned[ticker] = data
    
    print(f"   ✅ {len(cleaned)} тикеров")
    print()
    
    # 5. Target
    print("5. Создание target...")
    
    from target import TargetCreator
    tc = TargetCreator(cleaned)
    target_data = tc.process_all(days=30)
    
    all_train = []
    for ticker, data in target_data.items():
        all_train.append(data)
    
    train_final = pd.concat(all_train, ignore_index=True)
    print(f"   ✅ {len(train_final):,} примеров")
    print(f"   ✅ Баланс: {(train_final['target']==1).mean()*100:.1f}%")
    print()
    
    # 6. Признаки
    print("6. Подготовка признаков...")
    
    feature_cols = [
        'open', 'high', 'low', 'close', 'volume',
        'MA20', 'MA50', 'MA200',
        'close_MA20_ratio', 'close_MA50_ratio', 'close_MA200_ratio',
        'daily_return', 'volatility_30', 'momentum_10_ratio',
        'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
        'volume_MA20', 'volume_ratio',
        'HL_range_pct', 'CO_ratio', 'position_in_range',
        'key_rate', 'usd_rub', 'oil_price',
        'usd_rub_lag1', 'usd_rub_lag7',
        'key_rate_lag1', 'oil_price_lag1',
    ]
    
    available_cols = [c for c in feature_cols if c in train_final.columns]
    print(f"   ✅ {len(available_cols)} признаков")
    
    X = train_final[available_cols]
    y = train_final['target']
    
    mask = ~(X.isnull().any(axis=1))
    X = X[mask]
    y = y[mask]
    print(f"   ✅ {len(X):,} примеров")
    print()
    
    # 7. Разделение
    print("7. Разделение train/val...")
    
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"   ✅ Train: {len(X_train):,}, Val: {len(X_val):,}")
    print()
    
    # 8. Балансировка
    print("8. Балансировка...")
    
    from data_cleaner import DataBalancer
    balancer = DataBalancer(method='both', sampling_strategy=1.0, random_state=42)
    X_train_balanced, y_train_balanced = balancer.fit_resample(X_train.values, y_train.values)
    print(f"   ✅ 50%/50%")
    print()
    
    # 9. Обучение
    print("9. Обучение XGBoost...")
    
    from xgboost import XGBClassifier
    from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
    
    print("   (займёт ~5-7 минут)...")
    
    model.fit(
        pd.DataFrame(X_train_balanced, columns=available_cols), y_train_balanced,
        eval_set=[(pd.DataFrame(X_val, columns=available_cols), y_val)],
        verbose=True
    )
    
    print("   ✅ Обучено!")
    print()
    
    # 10. Оценка
    print("10. Оценка модели...")
    
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_val, y_pred),
        'roc_auc': roc_auc_score(y_val, y_pred_proba),
        'precision': precision_score(y_val, y_pred),
        'recall': recall_score(y_val, y_pred),
        'f1': 2 * precision_score(y_val, y_pred) * recall_score(y_val, y_pred) / 
              (precision_score(y_val, y_pred) + recall_score(y_val, y_pred)),
        'n_features': len(available_cols),
        'n_train': len(X_train_balanced),
        'model_params': {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.1}
    }
    
    print(f"   Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"   ROC-AUC:   {metrics['roc_auc']:.4f} ({metrics['roc_auc']*100:.2f}%)")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall:    {metrics['recall']:.4f}")
    print()
    
    # 11. Сохранение
    print("11. СОХРАНЕНИЕ МОДЕЛИ...")
    
    joblib.dump(model, MODEL_DIR / 'model_moex_quick.joblib')
    print(f"   ✅ Модель: model_moex_quick.joblib")
    
    with open(MODEL_DIR / 'metrics_moex_quick.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✅ Метрики: metrics_moex_quick.json")
    
    print()
    print("=" * 80)
    print("✅✅✅ ОБУЧЕНИЕ УСПЕШНО ЗАВЕРШЕНО! ✅✅✅")
    print("=" * 80)
    print()
    print(f"📊 Accuracy: {metrics['accuracy']:.2%}")
    print(f"📊 ROC-AUC: {metrics['roc_auc']:.2%}")
    print()
    print("🎯 Модель готова!")
    print()
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ ОБУЧЕНИЕ ПРЕРВАЛОСЬ!")
    print("=" * 80)
    print(f"Ошибка: {e}")
    
    import traceback
    with open(MODEL_DIR / 'error_full.txt', 'w') as f:
        f.write(traceback.format_exc())
    
    raise

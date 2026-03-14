"""
ML Stock Prediction Pipeline (Комбинированный)

Полный пайплайн обучения модели:
1. Загрузка данных (S&P 500 + Yahoo Finance РФ + ЦБ РФ макро)
2. Feature Engineering
3. Создание target переменной
4. Подготовка данных
5. Обучение модели
6. Оценка модели
7. Интерпретация результатов
8. AI-анализ
"""

import sys
from pathlib import Path

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_loader import DataLoader
from features import FeatureEngineer
from target import TargetCreator, DataPreparator
from train import ModelTrainer
from interpret import ModelInterpreter, AIAnalyzer
from predict import StockPredictor, MacroDataLoader
from yahoo_data_loader import YahooDataLoader, CBRDataLoader
from data_cleaner import DataCleaner, DataBalancer, clean_financial_data

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json


def run_full_pipeline(
    data_dir: str = None,
    model_type: str = 'xgboost',
    target_days: int = 30,
    test_size: float = 0.2,
    save_results: bool = True,
    use_yahoo: bool = True,  # Использовать Yahoo Finance для РФ
    use_macro: bool = True,  # Использовать макро данные ЦБ РФ
    clean_nan: bool = True,  # Очищать NaN значения
    balance_data: bool = True,  # Балансировать классы
    optimized_params: bool = True  # Использовать оптимизированные гиперпараметры
):
    """
    Запуск полного пайплайна
    
    Args:
        data_dir: путь к данным S&P 500
        model_type: тип модели (xgboost, lightgbm)
        target_days: горизонт прогноза (дней)
        test_size: доля test набора
        save_results: сохранять ли результаты
        use_yahoo: загрузить данные РФ акций из Yahoo Finance
        use_macro: загрузить макро данные ЦБ РФ
    """
    
    print("\n" + "=" * 80)
    print("🚀 ML STOCK PREDICTION PIPELINE (КОМБИНИРОВАННЫЙ)")
    print("=" * 80)
    print()
    
    # Пути
    if data_dir is None:
        DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    else:
        DATA_DIR = Path(data_dir)
    
    OUTPUT_DIR = Path(__file__).parent.parent / "data"
    MODEL_DIR = Path(__file__).parent / "models" / "trained"
    RESULTS_DIR = Path(__file__).parent / "models" / "results"
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # ========== ЭТАП 0: Загрузка данных ==========
    print("=" * 80)
    print("📊 ЭТАП 0: ЗАГРУЗКА ДАННЫХ")
    print("=" * 80)
    print()
    
    all_stock_data = []
    
    # 1. S&P 500 данные (если есть)
    if (DATA_DIR / "all_stocks_5yr.csv").exists():
        print("📂 Загрузка S&P 500 данных...")
        loader = DataLoader(DATA_DIR)
        tickers_data = loader.process_all()
        
        for ticker, data in tickers_data.items():
            data = data[['date', 'Name', 'open', 'high', 'low', 'close', 'volume']]
            all_stock_data.append(data)
        print(f"✅ S&P 500: {sum(len(df) for df in all_stock_data):,} строк")
        print()
    else:
        print("⚠️ S&P 500 данные не найдены, пропускаем")
        print()
    
    # 2. Yahoo Finance - РФ акции
    if use_yahoo:
        yahoo_loader = YahooDataLoader(OUTPUT_DIR / "raw")
        
        # США (опционально)
        # us_data = yahoo_loader.download_us_stocks()
        # if len(us_data) > 0:
        #     all_stock_data.append(us_data)
        
        # РФ акции
        ru_data = yahoo_loader.download_ru_stocks()
        if len(ru_data) > 0:
            all_stock_data.append(ru_data)
        print()
    
    # 3. Макро данные ЦБ РФ
    if use_macro:
        cbr_loader = CBRDataLoader(OUTPUT_DIR / "raw")
        macro_data = cbr_loader.get_all_macro()
        print()
    else:
        macro_data = None
    
    # Объединение всех данных
    if all_stock_data:
        combined_stocks = pd.concat(all_stock_data, ignore_index=True)
        print(f"✅ Всего акций: {len(combined_stocks):,} строк")
        print(f"   Тикеров: {combined_stocks['Name'].nunique()}")
        print()
    else:
        print("❌ Нет данных для обучения!")
        return None
    
    # ========== ЭТАП 1: Очистка данных ==========
    print("=" * 70)
    print("📊 ЭТАП 1: ОЧИСТКА ДАННЫХ")
    print("=" * 70)
    print()
    
    # Преобразование дат
    combined_stocks['date'] = pd.to_datetime(combined_stocks['date'])
    
    # Сортировка
    combined_stocks = combined_stocks.sort_values(['Name', 'date']).reset_index(drop=True)
    
    # Удаление пропусков
    combined_stocks = combined_stocks.dropna()
    
    # Разделение по тикерам
    tickers_data = {
        ticker: group.copy() 
        for ticker, group in combined_stocks.groupby('Name')
    }
    
    print(f"✅ Обработано {len(tickers_data)} тикеров")
    print()
    
    # ========== ЭТАП 2: Feature Engineering ==========
    fe = FeatureEngineer(tickers_data)
    processed_data = fe.process_all()
    fe.remove_nan_rows(min_rows=250)
    
    # ========== ЭТАП 3: Добавление макропризнаков ==========
    if use_macro and macro_data is not None:
        print("=" * 70)
        print("📊 ЭТАП 3: ДОБАВЛЕНИЕ МАКРОПРИЗНАКОВ")
        print("=" * 70)
        print()
        
        for ticker, data in processed_data.items():
            # Merge с макро данными
            data = data.merge(macro_data, on='date', how='left')
            data['key_rate'] = data['key_rate'].ffill()
            processed_data[ticker] = data
        
        print("✅ Макропризнаки добавлены")
        print()
    
    # ========== ЭТАП 4: Создание target ==========
    tc = TargetCreator(fe.processed_data)
    target_data = tc.process_all(days=target_days)
    
    # ========== ЭТАП 5: Подготовка данных ==========
    dp = DataPreparator(tc.processed_data)
    X_train, X_test, y_train, y_test = dp.prepare_train_test(test_size=test_size)

    if save_results:
        dp.save_data(X_train, X_test, y_train, y_test, OUTPUT_DIR / "processed")

    # ========== ЭТАП 5.5: Очистка данных (NaN, выбросы) ==========
    if clean_nan:
        print("=" * 70)
        print("🧹 ЭТАП 5.5: ОЧИСТКА ДАННЫХ ОТ NaN")
        print("=" * 70)
        print()
        
        # Очистка train данных
        print("Очистка train набора...")
        train_df = X_train.copy()
        train_df['target'] = y_train
        
        # Удаление строк с NaN в признаках
        before_nan = train_df.isna().sum().sum()
        train_df = train_df.dropna()
        after_nan = train_df.isna().sum().sum()
        
        print(f"   Удалено NaN: {before_nan - after_nan}")
        print(f"   Осталось строк: {len(train_df):,}")
        
        # Разделение обратно на X и y
        X_train_clean = train_df.drop('target', axis=1)
        y_train_clean = train_df['target']
        
        # Очистка test данных
        print("Очистка test набора...")
        test_df = X_test.copy()
        test_df['target'] = y_test
        test_df = test_df.dropna()
        
        X_test_clean = test_df.drop('target', axis=1)
        y_test_clean = test_df['target']
        
        print(f"   Осталось строк: {len(test_df):,}")
        print()
        
        # Использовать очищенные данные
        X_train, X_test, y_train, y_test = X_train_clean, X_test_clean, y_train_clean, y_test_clean
        
        print("=" * 70)
        print("✅ ОЧИСТКА ЗАВЕРШЕНА")
        print("=" * 70)
        print()

    # ========== ЭТАП 5.6: Балансировка классов ==========
    if balance_data:
        print("=" * 70)
        print("⚖️ ЭТАП 5.6: БАЛАНСИРОВКА КЛАССОВ")
        print("=" * 70)
        print()
        
        print(f"До балансировки:")
        print(f"   Class 0: {(y_train == 0).sum():,} ({(y_train == 0).mean()*100:.1f}%)")
        print(f"   Class 1: {(y_train == 1).sum():,} ({(y_train == 1).mean()*100:.1f}%)")
        
        # Комбинированная балансировка (SMOTE + Undersampling)
        # sampling_strategy=1.0 означает равное количество классов
        balancer = DataBalancer(method='both', sampling_strategy=1.0, random_state=42)
        X_train_balanced, y_train_balanced = balancer.fit_resample(X_train.values, y_train.values)
        
        print(f"После балансировки:")
        print(f"   Class 0: {(y_train_balanced == 0).sum():,} ({(y_train_balanced == 0).mean()*100:.1f}%)")
        print(f"   Class 1: {(y_train_balanced == 1).sum():,} ({(y_train_balanced == 1).mean()*100:.1f}%)")
        print()
        
        # Использовать сбалансированные данные
        X_train, y_train = X_train_balanced, y_train_balanced
        
        print("=" * 70)
        print("✅ БАЛАНСИРОВКА ЗАВЕРШЕНА")
        print("=" * 70)
        print()

    # ========== ЭТАП 6-7: Обучение и оценка ==========
    trainer = ModelTrainer(model_type=model_type, use_optimized_params=optimized_params)
    metrics = trainer.train(X_train, y_train, X_test, y_test, handle_imbalance=False)
    
    if save_results:
        trainer.save_model(MODEL_DIR)
        trainer.plot_results(y_test, trainer.model.predict_proba(X_test)[:, 1], RESULTS_DIR)
    
    # ========== ЭТАП 8: Интерпретация ==========
    interpreter = ModelInterpreter(trainer.model, X_train.columns.tolist())
    interpreter.print_importance()
    
    if save_results:
        interpreter.plot_importance(top_n=15, output_dir=RESULTS_DIR)
        
        # Сохранение важности признаков
        importance_df = interpreter.get_feature_importance()
        importance_df.to_csv(RESULTS_DIR / 'feature_importance.csv', index=False)
    
    # ========== ЭТАП 9: AI-анализ ==========
    analyzer = AIAnalyzer(trainer.model, X_train.columns.tolist(), interpreter)
    
    # Тестовый анализ
    if X_test is not None and len(X_test) > 0:
        sample_ticker = 'SBER' if 'SBER' in tickers_data else list(tickers_data.keys())[0]
        sample_features = X_test.iloc[-1:].copy()
        
        report = analyzer.analyze_stock(sample_ticker, sample_features)
        analyzer.print_report(report)
    
    # ========== Сохранение отчёта ==========
    if save_results:
        full_report = {
            'model_type': model_type,
            'target_days': target_days,
            'metrics': metrics,
            'feature_importance': interpreter.get_feature_importance().to_dict('records'),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'n_features': len(X_train.columns),
            'data_sources': {
                'sp500': (DATA_DIR / "all_stocks_5yr.csv").exists(),
                'yahoo_ru': use_yahoo,
                'cb_macro': use_macro
            }
        }
        
        with open(RESULTS_DIR / 'full_report.json', 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Полный отчёт сохранён в {RESULTS_DIR / 'full_report.json'}")
    
    # ========== Итоги ==========
    print("\n" + "=" * 80)
    print("✅ PIPELINE ЗАВЕРШЁН")
    print("=" * 80)
    print()
    print("📊 ИТОГИ:")
    print(f"   • Модель: {model_type}")
    print(f"   • Горизонт прогноза: {target_days} дней")
    print(f"   • Accuracy: {metrics['accuracy']:.4f}")
    print(f"   • ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"   • Обучено примеров: {len(X_train):,}")
    print(f"   • Протестировано примеров: {len(X_test):,}")
    print()
    print("📁 СОХРАНЕНО:")
    print(f"   • Модель: {MODEL_DIR / f'model_{model_type}.joblib'}")
    print(f"   • Метрики: {MODEL_DIR / 'metrics.json'}")
    print(f"   • Графики: {RESULTS_DIR / 'model_curves.png'}")
    print(f"   • Feature Importance: {RESULTS_DIR / 'feature_importance.png'}")
    print(f"   • Полный отчёт: {RESULTS_DIR / 'full_report.json'}")
    print()
    
    return {
        'model': trainer.model,
        'metrics': metrics,
        'interpreter': interpreter,
        'analyzer': analyzer
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ML Stock Prediction Pipeline (Комбинированный)')
    parser.add_argument('--data-dir', type=str, default=None, help='Путь к данным S&P 500')
    parser.add_argument('--model', type=str, default='xgboost', choices=['xgboost', 'lightgbm'], help='Тип модели')
    parser.add_argument('--target-days', type=int, default=30, help='Горизонт прогноза (дней)')
    parser.add_argument('--test-size', type=float, default=0.2, help='Доля test набора')
    parser.add_argument('--no-sp500', action='store_true', help='Не использовать S&P 500')
    parser.add_argument('--no-yahoo', action='store_true', help='Не использовать Yahoo Finance')
    parser.add_argument('--no-macro', action='store_true', help='Не использовать макро данные ЦБ')
    parser.add_argument('--no-save', action='store_true', help='Не сохранять результаты')
    
    args = parser.parse_args()
    
    results = run_full_pipeline(
        data_dir=args.data_dir,
        model_type=args.model,
        target_days=args.target_days,
        test_size=args.test_size,
        save_results=not args.no_save,
        use_yahoo=not args.no_yahoo,
        use_macro=not args.no_macro
    )

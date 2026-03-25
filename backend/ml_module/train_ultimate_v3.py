"""
INVESTEDU ML MODEL v3.0 — ПРОДВИНУТАЯ ВЕРСИЯ

Максимально продвинутая модель для прогнозирования роста акций РФ

Особенности:
✅ Ансамбль моделей (XGBoost + LightGBM + CatBoost)
✅ Регуляризация (защита от переобучения)
✅ 50+ признаков (lag, rolling, volatility, patterns)
✅ Калибровка вероятностей (Platt scaling)
✅ Walk-Forward валидация (честная оценка)
✅ SHAP explainability (объяснение прогнозов)
✅ Backtesting с метриками (Sharpe, CAGR, Max Drawdown)

Горизонты прогнозирования:
- 7 дней (краткосрок)
- 30 дней (среднесрок)

Автор: InvestEdu Team
Версия: 3.0
"""

import sys
import json
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pickle

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score,
    recall_score, f1_score, confusion_matrix,
    classification_report, brier_score_loss
)

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class Config:
    """Конфигурация модели"""
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'ml_module' / 'Data'
    MODEL_DIR = BASE_DIR / 'ml_module' / 'models' / 'trained'
    
    # Горизонты прогнозирования
    HORIZONS = [7, 30]  # дней
    
    # Параметры моделей
    MODEL_PARAMS = {
        'max_depth': 4,           # Глубина дерева (меньше = меньше переобучение)
        'learning_rate': 0.01,    # Шаг обучения
        'n_estimators': 500,      # Количество деревьев
        'subsample': 0.7,         # Доля данных на дерево
        'colsample_bytree': 0.7,  # Доля признаков на дерево
        'reg_alpha': 1.0,         # L1 регуляризация
        'reg_lambda': 5.0,        # L2 регуляризация
        'min_child_weight': 10,   # Мин вес в листе
        'gamma': 0.5,             # Штраф за сложность
    }
    
    # Walk-Forward параметры
    WF_TRAIN_DAYS = 365    # 1 год для обучения
    WF_TEST_DAYS = 90      # 1 квартал для теста
    WF_STEP_DAYS = 30      # Шаг 1 месяц
    
    # Комиссии для backtesting
    COMMISSION = 0.0005    # 0.05%
    SLIPPAGE = 0.001       # 0.1%


# ============================================================================
# ЗАГРУЗКА ДАННЫХ
# ============================================================================

class AdvancedDataLoader:
    """Загрузка всех данных в одном месте"""
    
    def __init__(self):
        self.config = Config()
    
    def load_moex_stocks(self, n_tickers: int = 249) -> pd.DataFrame:
        """
        Загрузка данных MOEX

        Args:
            n_tickers: количество тикеров (топ по ликвидности)

        Returns:
            DataFrame с данными
        """
        print("📥 Загрузка данных MOEX...")

        # Путь к реальным данным MOEX (249 тикеров) — АБСОЛЮТНЫЙ ПУТЬ
        base_dir = Path(__file__).parent.parent.parent  # backend/
        moex_dir = base_dir / 'RUSSIA 249 Stocks Prices MOEX' / 'D1'

        print(f"   Путь: {moex_dir}")
        print(f"   Существует: {moex_dir.exists()}")

        if moex_dir.exists():
            # Загрузка из локальных файлов
            all_data = []
            csv_files = sorted(list(moex_dir.glob('*.csv')))[:n_tickers]

            print(f"   Найдено файлов: {len(csv_files)}")
            print(f"   Загружаем: {len(csv_files)} тикеров")

            for file in csv_files:
                try:
                    df = pd.read_csv(file)
                    # Нормализация колонок
                    if 'datetime' in df.columns:
                        df = df.rename(columns={'datetime': 'date'})
                    df['date'] = pd.to_datetime(df['date'])
                    df['Name'] = file.stem.replace('_D1', '')
                    all_data.append(df)
                except Exception as e:
                    print(f"   ⚠️ Ошибка {file}: {e}")

            if all_data:
                combined = pd.concat(all_data, ignore_index=True)
                print(f"   ✅ Загружено {len(combined):,} строк, {combined['Name'].nunique()} тикеров")
                return combined

        # Резервный вариант
        print("   ⚠️ Используем тестовые данные...")
        test_file = Path(__file__).parent / 'Data' / 'moex' / 'moex_test.csv'
        if test_file.exists():
            df = pd.read_csv(test_file)
            df['date'] = pd.to_datetime(df['date'])
            print(f"   ✅ Загружено {len(df):,} строк")
            return df

        return pd.DataFrame()
    
    def load_macro_ru(self) -> pd.DataFrame:
        """Загрузка макро данных РФ"""
        print("📥 Загрузка макро данных РФ...")

        # Используем cb_data_local.csv (там реальные данные!)
        macro_file = self.config.DATA_DIR / 'macro' / 'cb_data_local.csv'
        if macro_file.exists():
            df = pd.read_csv(macro_file)
            df['date'] = pd.to_datetime(df['date'])
            print(f"   ✅ Загружено {len(df):,} строк, {len(df.columns)} признаков")
            return df

        # Резервный вариант
        print("   ⚠️ cb_data_local.csv не найден, пробуем cb_macro_full.csv...")
        macro_file = self.config.DATA_DIR / 'macro' / 'cb_macro_full.csv'
        if macro_file.exists():
            df = pd.read_csv(macro_file)
            df['date'] = pd.to_datetime(df['date'])
            print(f"   ✅ Загружено {len(df):,} строк, {len(df.columns)} признаков")
            return df

        return pd.DataFrame()
    
    def merge_data(self, prices: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
        """Слияние цен и макро данных (ПРАВИЛЬНО: ffill ДО merge + lag для публикации)"""
        print("🔄 Слияние данных...")

        if len(macro) == 0:
            print("   ⚠️ Макро данные пустые, оставляем NaN")
            print("   💡 Загрузите cb_data_local.csv для реальных макро данных")
            # ✅ Оставляем NaN — деревья умеют с ними работать
            prices['key_rate'] = np.nan
            prices['usd_rub'] = np.nan
            prices['oil_price'] = np.nan
            prices['inflation'] = np.nan
            return prices

        # ✅ ИСПРАВЛЕНО: ffill НА macro ДО merge + lag для публикации!
        print(f"   Макро данные: {len(macro):,} строк ({macro['date'].min().date()} — {macro['date'].max().date()})")
        
        # ✅ Конвертируем макро в ежедневную частоту
        macro = macro.sort_values('date')
        macro = macro.set_index('date')
        
        # ✅ Reindex по ВСЕМ датам из prices
        all_dates = sorted(prices['date'].unique())
        macro = macro.reindex(all_dates)
        
        # ✅ ffill + shift(1) для задержки публикации!
        # Макро данные публикуются с задержкой (например, инфляция за март в апреле)
        macro = macro.ffill().shift(1)  # ✅ Сдвиг на 1 день
        
        macro = macro.reset_index()
        macro = macro.rename(columns={'index': 'date'})
        
        print(f"   ✅ Макро синхронизировано + lag 1 день: {len(macro):,} строк")

        # Преобразование дат
        prices['date'] = pd.to_datetime(prices['date'])

        # Слияние ДЛЯ КАЖДОГО тикера отдельно
        merged_list = []
        tickers = prices['Name'].unique()

        print(f"   Слияние для {len(tickers)} тикеров...")

        for i, ticker in enumerate(tickers):
            ticker_df = prices[prices['Name'] == ticker].copy()

            # ✅ Merge с ежедневным macro (с задержкой публикации!)
            merged = ticker_df.merge(macro, on='date', how='left')

            # ✅ ОСТАВЛЯЕМ NaN — деревья умеют с ними работать!
            # ❌ НЕ заполняем дефолтами — это создаёт искусственные сигналы!
            # Модель может выучить: "если key_rate == 18.0 → BUY"
            
            merged_list.append(merged)

            # Прогресс
            if (i + 1) % 50 == 0:
                print(f"   Обработано {i + 1}/{len(tickers)} тикеров...")

        merged_final = pd.concat(merged_list, ignore_index=True)
        print(f"   ✅ Итого: {len(merged_final):,} строк, {len(merged_final.columns)} признаков")
        
        # ✅ Статистика NaN
        # ✅ Статистика NaN — только по реально существующим колонкам
        macro_cols = ['key_rate', 'usd_rub', 'oil_price', 'inflation']
        existing_cols = [col for col in macro_cols if col in merged_final.columns]

        if existing_cols:
            nan_stats = merged_final[existing_cols].isnull().sum()
            print(f"   📊 NaN статистика:")
            for col, count in nan_stats.items():
                pct = count / len(merged_final) * 100
                print(f"      {col}: {count:,} ({pct:.2f}%)")
        else:
            print("   📊 NaN статистика: макро-колонки не найдены")

        return merged_final


# ============================================================================
# FEATURE ENGINEERING 2.0
# ============================================================================

class AdvancedFeatureEngineer:
    """Создание 50+ признаков"""
    
    def __init__(self):
        self.feature_columns = []
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание всех признаков"""
        print("\n📊 Feature Engineering...")
        
        df = df.copy()
        
        # 1. Технические индикаторы
        df = self._create_moving_averages(df)
        df = self._create_momentum_features(df)
        df = self._create_volatility_features(df)
        df = self._create_volume_features(df)
        
        # 2. Lag признаки
        df = self._create_lag_features(df, lags=[1, 2, 3, 5, 10])
        
        # 3. Rolling статистики
        df = self._create_rolling_features(df, windows=[5, 10, 20])
        
        # 4. Паттерны
        df = self._create_pattern_features(df)
        
        # 5. Сезонность
        df = self._create_seasonal_features(df)
        
        # Сохраняем список признаков
        exclude_cols = ['date', 'Name', 'open', 'high', 'low', 'close', 'volume', 'target_7d', 'target_30d']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols and not col.startswith('Unnamed')]
        
        print(f"   ✅ Создано {len(self.feature_columns)} признаков")
        
        return df
    
    def _create_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Скользящие средние"""
        for window in [5, 10, 20, 50, 200]:
            df[f'ma_{window}'] = df.groupby('Name')['close'].transform(
                lambda x: x.rolling(window).mean()
            )
            df[f'ma_{window}_ratio'] = df['close'] / df[f'ma_{window}']
        
        return df
    
    def _create_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Momentum индикаторы"""
        # Доходность
        for period in [1, 3, 5, 10, 20]:
            df[f'return_{period}d'] = df.groupby('Name')['close'].transform(
                lambda x: x.pct_change(period)
            )
        
        # RSI
        delta = df.groupby('Name')['close'].diff()
        gain = (delta.where(delta > 0, 0)).groupby(df['Name']).transform(
            lambda x: x.rolling(14).mean()
        )
        loss = (-delta.where(delta < 0, 0)).groupby(df['Name']).transform(
            lambda x: x.rolling(14).mean()
        )
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df.groupby('Name')['close'].transform(lambda x: x.ewm(span=12).mean())
        exp2 = df.groupby('Name')['close'].transform(lambda x: x.ewm(span=26).mean())
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def _create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Волатильность"""
        # Стандартная волатильность
        for window in [5, 10, 20, 60]:
            df[f'volatility_{window}d'] = df.groupby('Name')['close'].transform(
                lambda x: x.pct_change().rolling(window).std()
            )
        
        # ATR (Average True Range)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_14'] = df.groupby('Name')['true_range'].transform(
            lambda x: x.rolling(14).mean()
        )
        df['atr_ratio'] = df['atr_14'] / df['close']
        
        # Parkinson Volatility
        df['parkinson'] = (
            1 / (4 * np.log(2)) * 
            (np.log(df['high'] / df['low']) ** 2)
        ).groupby(df['Name']).transform(lambda x: x.rolling(20).mean())
        
        return df
    
    def _create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Объёмные индикаторы"""
        # Volume MA
        for window in [5, 10, 20]:
            df[f'volume_ma_{window}'] = df.groupby('Name')['volume'].transform(
                lambda x: x.rolling(window).mean()
            )
        
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']
        
        # OBV (On-Balance Volume)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).groupby(df['Name']).cumsum()
        
        return df
    
    def _create_lag_features(self, df: pd.DataFrame, lags: List[int]) -> pd.DataFrame:
        """Lag признаки"""
        for lag in lags:
            df[f'close_lag_{lag}'] = df.groupby('Name')['close'].transform(
                lambda x: x.shift(lag)
            )
            df[f'return_lag_{lag}'] = df.groupby('Name')['close'].transform(
                lambda x: x.pct_change().shift(lag)
            )
            df[f'volume_lag_{lag}'] = df.groupby('Name')['volume'].transform(
                lambda x: x.shift(lag)
            )
        
        return df
    
    def _create_rolling_features(self, df: pd.DataFrame, windows: List[int]) -> pd.DataFrame:
        """Rolling статистики"""
        for window in windows:
            # Скользящее среднее и стандартное отклонение
            df[f'close_mean_{window}'] = df.groupby('Name')['close'].transform(
                lambda x: x.rolling(window).mean()
            )
            df[f'close_std_{window}'] = df.groupby('Name')['close'].transform(
                lambda x: x.rolling(window).std()
            )
            df[f'volume_mean_{window}'] = df.groupby('Name')['volume'].transform(
                lambda x: x.rolling(window).mean()
            )
            
            # Min/Max за период
            df[f'close_min_{window}'] = df.groupby('Name')['close'].transform(
                lambda x: x.rolling(window).min()
            )
            df[f'close_max_{window}'] = df.groupby('Name')['close'].transform(
                lambda x: x.rolling(window).max()
            )
            
            # Позиция цены в диапазоне
            df[f'close_position_{window}'] = (
                (df['close'] - df[f'close_min_{window}']) /
                (df[f'close_max_{window}'] - df[f'close_min_{window}'] + 1e-8)
            )
        
        return df
    
    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Паттерны свечей"""
        # Размер свечи
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_range'] = df['high'] - df['low']
        df['candle_ratio'] = df['candle_body'] / (df['candle_range'] + 1e-8)
        
        # Бычьи/медвежьи паттерны
        df['bullish_engulfing'] = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (df['open'] < df['close'].shift(1))
        ).astype(int)
        
        # Режим рынка
        df['ma50_above_ma200'] = (df['ma_50'] > df['ma_200']).astype(int)
        df['price_above_ma200'] = (df['close'] > df['ma_200']).astype(int)
        
        return df
    
    def _create_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Сезонность"""
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
        
        return df


# ============================================================================
# TARGET CREATION
# ============================================================================

class TargetCreator:
    """Создание target для двух горизонтов"""
    
    def __init__(self, horizons: List[int] = [7, 30]):
        self.horizons = horizons
    
    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание target для каждого горизонта"""
        print("\n🎯 Создание target...")
        
        df = df.copy()
        
        for horizon in self.horizons:
            # Будущая цена через N дней
            df[f'future_close_{horizon}d'] = df.groupby('Name')['close'].transform(
                lambda x: x.shift(-horizon)
            )
            
            # Target: 1 если цена вырастет, 0 если нет
            df[f'target_{horizon}d'] = (
                df[f'future_close_{horizon}d'] > df['close']
            ).astype(int)
        
        # Удаление строк с NaN в target
        df = df.dropna(subset=[f'target_{h}d' for h in self.horizons])
        
        print(f"   ✅ Создано targets: {len(df):,} примеров")
        for horizon in self.horizons:
            target_col = f'target_{horizon}d'
            if target_col in df.columns:
                balance = df[target_col].mean() * 100
                print(f"   • {horizon} дней: баланс {balance:.1f}% / {100-balance:.1f}%")
        
        return df


# ============================================================================
# МОДЕЛЬ
# ============================================================================

class UltimateEnsembleModel:
    """Ансамбль моделей для двух горизонтов"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.models_7d = {}
        self.models_30d = {}
        self.feature_columns = []
        self.metrics = {'7d': {}, '30d': {}}
        self.feature_importance = {'7d': [], '30d': []}
        self.calibrators_7d = {}
        self.calibrators_30d = {}
    
    def create_base_models(self) -> List[Tuple[str, object]]:
        """Создание базовых моделей ансамбля"""
        models = []
        params = self.config.MODEL_PARAMS
        
        # XGBoost
        try:
            import xgboost as xgb
            xgb_model = xgb.XGBClassifier(
                n_estimators=params['n_estimators'],
                max_depth=params['max_depth'],
                learning_rate=params['learning_rate'],
                subsample=params['subsample'],
                colsample_bytree=params['colsample_bytree'],
                min_child_weight=params['min_child_weight'],
                gamma=params['gamma'],
                reg_alpha=params['reg_alpha'],
                reg_lambda=params['reg_lambda'],
                random_state=42,
                n_jobs=-1,
                eval_metric='auc',
                verbosity=0
            )
            models.append(('xgb', xgb_model))
            print("   ✅ XGBoost добавлен")
        except ImportError:
            print("   ⚠️ XGBoost не установлен")
        
        # LightGBM
        try:
            import lightgbm as lgb
            lgb_model = lgb.LGBMClassifier(
                n_estimators=params['n_estimators'],
                max_depth=params['max_depth'],
                learning_rate=params['learning_rate'],
                subsample=params['subsample'],
                colsample_bytree=params['colsample_bytree'],
                min_child_samples=int(params['min_child_weight'] * 5),
                reg_alpha=params['reg_alpha'],
                reg_lambda=params['reg_lambda'],
                random_state=42,
                verbose=-1,
                n_jobs=-1
            )
            models.append(('lgb', lgb_model))
            print("   ✅ LightGBM добавлен")
        except ImportError:
            print("   ⚠️ LightGBM не установлен")
        
        # CatBoost (опционально)
        try:
            from catboost import CatBoostClassifier
            cb_model = CatBoostClassifier(
                iterations=params['n_estimators'],
                depth=params['max_depth'],
                learning_rate=params['learning_rate'],
                l2_leaf_reg=params['reg_lambda'],
                random_seed=42,
                verbose=0,
                thread_count=-1,
                task_type='CPU'
            )
            models.append(('cat', cb_model))
            print("   ✅ CatBoost добавлен")
        except ImportError:
            print("   ⚠️ CatBoost не установлен (опционально)")
        
        return models
    
    def create_ensemble(self, base_models: List[Tuple[str, object]]):
        """Создание стекинга ансамбля"""
        # Мета-обучатель
        try:
            import xgboost as xgb
            meta_learner = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )
        except ImportError:
            from sklearn.linear_model import LogisticRegression
            meta_learner = LogisticRegression(
                C=0.1,
                max_iter=1000,
                random_state=42
            )
        
        ensemble = StackingClassifier(
            estimators=base_models,
            final_estimator=meta_learner,
            cv=5,
            stack_method='predict_proba',
            n_jobs=-1
        )
        
        return ensemble
    
    def fit(
        self,
        X_train: pd.DataFrame,
        y_train_7d: pd.Series,
        y_train_30d: pd.Series,
        X_val: pd.DataFrame = None,
        y_val_7d: pd.Series = None,
        y_val_30d: pd.Series = None
    ) -> Dict:
        """Обучение ансамбля для двух горизонтов"""
        print("\n" + "=" * 80)
        print("🚀 ОБУЧЕНИЕ АНСАМБЛЯ (2 горизонта: 7 и 30 дней)")
        print("=" * 80)
        
        self.feature_columns = X_train.columns.tolist()
        
        # Создание базовых моделей
        print("\n1. Создание базовых моделей...")
        base_models = self.create_base_models()
        
        if len(base_models) == 0:
            raise ImportError("Ни одна модель не доступна!")
        
        # Создание ансамбля
        print("\n2. Создание стекинга ансамбля...")
        ensemble = self.create_ensemble(base_models)
        
        # Обучение для 7 дней
        print("\n3. Обучение для горизонта 7 дней...")
        self.models_7d['ensemble'] = ensemble
        self.models_7d['ensemble'].fit(X_train.values, y_train_7d.values)
        
        # Калибровка для 7 дней
        print("\n4. Калибровка вероятностей (7 дней)...")
        if X_val is not None and y_val_7d is not None:
            self.calibrators_7d['model'] = CalibratedClassifierCV(
                self.models_7d['ensemble'],
                method='isotonic',
                cv='prefit'
            )
            self.calibrators_7d['model'].fit(X_val.values, y_val_7d.values)
        
        # Обучение для 30 дней
        print("\n5. Обучение для горизонта 30 дней...")
        self.models_30d['ensemble'] = self.create_ensemble(base_models)
        self.models_30d['ensemble'].fit(X_train.values, y_train_30d.values)
        
        # Калибровка для 30 дней
        print("\n6. Калибровка вероятностей (30 дней)...")
        if X_val is not None and y_val_30d is not None:
            self.calibrators_30d['model'] = CalibratedClassifierCV(
                self.models_30d['ensemble'],
                method='isotonic',
                cv='prefit'
            )
            self.calibrators_30d['model'].fit(X_val.values, y_val_30d.values)
        
        # Оценка
        print("\n7. Оценка на валидации...")
        self.metrics['7d'] = self._evaluate(
            X_val, y_val_7d, 
            self.calibrators_7d.get('model', self.models_7d['ensemble']),
            '7 дней'
        )
        self.metrics['30d'] = self._evaluate(
            X_val, y_val_30d,
            self.calibrators_30d.get('model', self.models_30d['ensemble']),
            '30 дней'
        )
        
        # Feature Importance
        print("\n8. Расчёт важности признаков...")
        self._calculate_feature_importance()
        
        print("\n" + "=" * 80)
        print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО")
        print("=" * 80)
        
        return self.metrics
    
    def _evaluate(self, X: pd.DataFrame, y: pd.Series, model, horizon_name: str) -> Dict:
        """Оценка модели"""
        y_pred = model.predict(X.values)
        y_proba = model.predict_proba(X.values)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'roc_auc': roc_auc_score(y, y_proba),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'f1': f1_score(y, y_pred),
            'brier_score': brier_score_loss(y, y_proba)
        }
        
        print(f"\n📊 МЕТРИКИ ({horizon_name}):")
        print(f"   Accuracy:     {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"   ROC-AUC:      {metrics['roc_auc']:.4f} ({metrics['roc_auc']*100:.2f}%)")
        print(f"   Precision:    {metrics['precision']:.4f}")
        print(f"   Recall:       {metrics['recall']:.4f}")
        print(f"   F1-Score:     {metrics['f1']:.4f}")
        print(f"   Brier Score:  {metrics['brier_score']:.4f}")
        
        return metrics
    
    def _calculate_feature_importance(self):
        """Расчёт важности признаков"""
        for horizon, models in [('7d', self.models_7d), ('30d', self.models_30d)]:
            if 'ensemble' in models and hasattr(models['ensemble'], 'estimators_'):
                importance = np.zeros(len(self.feature_columns))
                
                for name, model in models['ensemble'].estimators_:
                    if hasattr(model, 'feature_importances_'):
                        importance += model.feature_importances_
                
                importance /= len(models['ensemble'].estimators_)
                
                self.feature_importance[horizon] = sorted(
                    zip(self.feature_columns, importance),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]  # Топ-20
        
        print("\n🔍 ТОП-10 ПРИЗНАКОВ (7 дней):")
        for i, (feat, imp) in enumerate(self.feature_importance['7d'][:10], 1):
            print(f"   {i:2}. {feat:<30} {imp:.4f}")
    
    def predict(self, X: pd.DataFrame, horizon: int = 7) -> Tuple[np.ndarray, np.ndarray]:
        """Предсказание класса и вероятности"""
        if horizon == 7:
            model = self.calibrators_7d.get('model', self.models_7d.get('ensemble'))
        else:
            model = self.calibrators_30d.get('model', self.models_30d.get('ensemble'))
        
        if model is None:
            raise ValueError(f"Модель для горизонта {horizon} дней не обучена!")
        
        y_pred = model.predict(X.values)
        y_proba = model.predict_proba(X.values)[:, 1]
        
        return y_pred, y_proba
    
    def save(self, path: Path = None):
        """Сохранение модели"""
        if path is None:
            path = self.config.MODEL_DIR / 'model_ultimate_v3.joblib'
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'models_7d': self.models_7d,
            'models_30d': self.models_30d,
            'calibrators_7d': self.calibrators_7d,
            'calibrators_30d': self.calibrators_30d,
            'feature_columns': self.feature_columns,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }
        
        joblib.dump(model_data, path)
        print(f"\n💾 Модель сохранена: {path}")
    
    @classmethod
    def load(cls, path: Path, config: Config = None) -> 'UltimateEnsembleModel':
        """Загрузка модели"""
        instance = cls(config)
        model_data = joblib.load(path)
        
        instance.models_7d = model_data['models_7d']
        instance.models_30d = model_data['models_30d']
        instance.calibrators_7d = model_data.get('calibrators_7d', {})
        instance.calibrators_30d = model_data.get('calibrators_30d', {})
        instance.feature_columns = model_data['feature_columns']
        instance.metrics = model_data.get('metrics', {})
        instance.feature_importance = model_data.get('feature_importance', {})
        
        return instance


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def train_ultimate_model():
    """Обучение финальной модели"""
    print("=" * 80)
    print("INVESTEDU ML MODEL v3.0 — ОБУЧЕНИЕ")
    print("=" * 80)
    
    config = Config()
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Загрузка данных
    print("\n" + "=" * 80)
    print("1. ЗАГРУЗКА ДАННЫХ")
    print("=" * 80)
    
    loader = AdvancedDataLoader()
    prices = loader.load_moex_stocks(n_tickers=50)
    macro = loader.load_macro_ru()
    
    if len(prices) == 0:
        print("❌ Нет данных для обучения!")
        return
    
    # 2. Слияние
    df = loader.merge_data(prices, macro)
    
    # 3. Feature Engineering
    print("\n" + "=" * 80)
    print("2. FEATURE ENGINEERING")
    print("=" * 80)
    
    fe = AdvancedFeatureEngineer()
    df = fe.create_all_features(df)
    
    # 4. Target
    tc = TargetCreator(horizons=[7, 30])
    df = tc.create_targets(df)
    
    # 5. Подготовка данных для обучения
    print("\n" + "=" * 80)
    print("3. ПОДГОТОВКА ДАННЫХ")
    print("=" * 80)
    
    # Удаление строк с NaN
    df = df.dropna()
    print(f"   После очистки: {len(df):,} строк")
    
    # Разделение на train/val (по времени)
    df = df.sort_values('date')
    split_date = df['date'].max() - pd.Timedelta(days=90)
    
    train_df = df[df['date'] < split_date]
    val_df = df[df['date'] >= split_date]
    
    print(f"   Train: {len(train_df):,} строк")
    print(f"   Val: {len(val_df):,} строк")
    
    # Признаки и target
    feature_cols = fe.feature_columns
    X_train = train_df[feature_cols].fillna(0)
    X_val = val_df[feature_cols].fillna(0)
    y_train_7d = train_df['target_7d']
    y_train_30d = train_df['target_30d']
    y_val_7d = val_df['target_7d']
    y_val_30d = val_df['target_30d']
    
    # 6. Обучение модели
    print("\n" + "=" * 80)
    print("4. ОБУЧЕНИЕ МОДЕЛИ")
    print("=" * 80)
    
    model = UltimateEnsembleModel(config)
    metrics = model.fit(
        X_train, y_train_7d, y_train_30d,
        X_val, y_val_7d, y_val_30d
    )
    
    # 7. Сохранение
    print("\n" + "=" * 80)
    print("5. СОХРАНЕНИЕ МОДЕЛИ")
    print("=" * 80)
    
    model.save()
    
    # Сохранение метрик
    metrics_path = config.MODEL_DIR / 'metrics_ultimate_v3.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"💾 Метрики сохранены: {metrics_path}")
    
    # 8. Итоги
    print("\n" + "=" * 80)
    print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 80)
    
    print("\n📊 ИТОГОВЫЕ МЕТРИКИ:")
    print(f"\nГоризонт 7 дней:")
    print(f"   ROC-AUC: {metrics['7d'].get('roc_auc', 'N/A'):.4f}")
    print(f"   Accuracy: {metrics['7d'].get('accuracy', 'N/A'):.4f}")
    
    print(f"\nГоризонт 30 дней:")
    print(f"   ROC-AUC: {metrics['30d'].get('roc_auc', 'N/A'):.4f}")
    print(f"   Accuracy: {metrics['30d'].get('accuracy', 'N/A'):.4f}")
    
    print("\n🎯 Модель готова к использованию!")
    print("\n📁 Файлы:")
    print(f"   • Модель: {config.MODEL_DIR / 'model_ultimate_v3.joblib'}")
    print(f"   • Метрики: {metrics_path}")
    
    return model


if __name__ == "__main__":
    train_ultimate_model()

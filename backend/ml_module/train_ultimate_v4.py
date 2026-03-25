import sys
import json
import warnings
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import pickle
import traceback

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
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectFromModel
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent))
def setup_logger(name: str, log_file: str = None):
    """Настройка логирования"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler (без эмодзи для Windows)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (с UTF-8 для поддержки эмодзи)
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

logger = setup_logger('ML_v4', 'ml_module/logs/train_v4.log')

class Config:
    """Продвинутая конфигурация"""
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'ml_module' / 'Data'
    MODEL_DIR = BASE_DIR / 'ml_module' / 'models' / 'trained'
    LOGS_DIR = BASE_DIR / 'ml_module' / 'logs'
    
    # Горизонты прогнозирования
    HORIZONS = [7, 30]  # дней (90 удалён — сильный дисбаланс)

    # Optuna
    OPTUNA_TRIALS = 2  # 100 итераций для максимального качества
    OPTUNA_TIMEOUT = 32400  # 9 часов таймаут (100 итераций × ~5 минут)

    # Purged CV
    CV_SPLITS = 5
    GAP_DAYS = 30  # Gap между train и test для защиты от утечки

    # Разделение ПО ВРЕМЕНИ (не по тикерам!)
    # Данные: 1999-2024 (25 лет)
    # Train: 1999-2019 (21 год) — достаточно для обучения
    # Val: 2020-2022 (3 года) — валидация + настройка гиперпараметров
    # Test: 2023-2024 (2 года) — финальный тест
    
    BASE_YEAR = 1999  # Начало данных
    TRAIN_END_YEAR = 2020  # Train: 1999-2019
    VAL_START_YEAR = 2020  # Val: 2020-2022
    TEST_START_YEAR = 2023  # Test: 2023-2024 (август)

    # Ранняя остановка
    EARLY_STOPPING_ROUNDS = 50

    # Feature Selection
    MAX_FEATURES = 100  # Максимум признаков
    FEATURE_THRESHOLD = 0.01  # Порог важности

    # Комиссии для backtesting
    COMMISSION = 0.0005
    SLIPPAGE = 0.001

    USE_SMOTE = False  # ❌ SMOTE для time series = leakage!
    USE_SCALE_POS_WEIGHT = True  # ✅ Правильный подход для финансов

    # Triple Barrier Method (3 класса)
    TB_PT_RATIO = 0.02  # TP threshold: return > 2%
    TB_SL_RATIO = 0.01  # SL threshold: return < -1%
    TB_WINDOW = 20  # Горизонт в днях

    # Early Stopping
    EARLY_STOPPING_ROUNDS = 50  # Остановить если нет улучшений
    MAX_ITERATIONS = 1000  # Максимум итераций

class DataValidator:
    """Проверка и очистка данных"""
    
    @staticmethod
    def validate(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Валидация данных
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        warnings = []
        
        # 1. Проверка минимума данных
        if len(df) < 60:
            errors.append(f"Мало данных: {len(df)} < 60 (минимум)")
        elif len(df) < 200:
            warnings.append(f"Мало данных: {len(df)} < 200 (рекомендуется)")
        
        # 2. Проверка необходимых колонок
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            errors.append(f"Отсутствуют колонки: {missing}")
        
        # 3. Проверка пропусков
        if len(df) > 0:
            missing_counts = df.isnull().sum()
            cols_with_missing = missing_counts[missing_counts > 0]
            if len(cols_with_missing) > 0:
                for col, count in cols_with_missing.items():
                    pct = count / len(df) * 100
                    if pct > 10:
                        errors.append(f"Много пропусков в {col}: {count} ({pct:.1f}%)")
                    else:
                        warnings.append(f"Пропуски в {col}: {count} ({pct:.1f}%)")
        
        # 4. Проверка выбросов (Z-score > 5)
        for col in ['close', 'volume']:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-8))
                outliers = (z_scores > 5).sum()
                if outliers > 0:
                    pct = outliers / len(df) * 100
                    warnings.append(f"Выбросы в {col}: {outliers} ({pct:.1f}%)")
        
        # 5. Проверка диапазона дат
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            date_range = (df['date'].max() - df['date'].min()).days
            if date_range < 60:
                errors.append(f"Малый период: {date_range} дней < 60")
        
        # 6. Проверка отрицательных цен (но НЕ volume — он исправляется в clean())
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns and (df[col] < 0).any():
                errors.append(f"Отрицательные значения в {col}")
        
        # 7. Проверка на дубликаты
        if 'date' in df.columns:
            dups = df.duplicated(subset=['date'], keep=False).sum()
            if dups > 0:
                warnings.append(f"Дубликаты дат: {dups}")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors, warnings
    
    @staticmethod
    def clean(df: pd.DataFrame, quantile_thresholds: dict = None) -> pd.DataFrame:
        """
        Очистка данных

        Args:
            df: DataFrame с данными
            quantile_thresholds: Пороги для winsorization (вычисляются на train)

        Returns:
            Очищенный DataFrame
        """
        df = df.copy()

        # 1. Удаление дубликатов (ПО ДАТЕ + ТИКЕРУ!)
        # ✅ Поддержка как 'Name' так и 'name'
        ticker_col = 'Name' if 'Name' in df.columns else 'name'
        
        if 'date' in df.columns and ticker_col in df.columns:
            df = df.drop_duplicates(subset=['date', ticker_col], keep='last')
        elif 'date' in df.columns:
            df = df.drop_duplicates(subset=['date'], keep='last')

        # 2. Сортировка по дате
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values([ticker_col, 'date']).reset_index(drop=True)

        # 3. Исправление отрицательного volume (по модулю)
        if 'volume' in df.columns:
            df['volume'] = df['volume'].abs()
            logger.info(f"   ✓ volume исправлен по модулю (отрицательные значения)")

        # 4. ❌ БЕЗ интерполяции! Только ffill для forward-fill
        # ✅ Интерполяция = leakage (знаем будущее)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns:
                # ✅ Только ffill (не знаем будущее)
                df[col] = df[col].ffill()
                # ❌ НЕ делать: df[col].interpolate()

        # 5. ❌ БЕЗ winsorization на всём датасете!
        # ✅ Пороги должны вычисляться ТОЛЬКО на train
        # Если переданы пороги — используем их
        if quantile_thresholds is not None:
            logger.info("   Применяем пороги winsorization из train")
            for col in ['close', 'volume']:
                if col in df.columns and col in quantile_thresholds:
                    q1, q99 = quantile_thresholds[col]
                    df[col] = df[col].clip(q1, q99)
        # else: не делаем winsorization здесь (будет сделано в pipeline)

        return df
    
    @staticmethod
    def compute_winsorization_thresholds(df: pd.DataFrame) -> dict:
        """
        Вычисление порогов для winsorization (только на train!)
        
        Args:
            df: DataFrame с данными (только train!)
        
        Returns:
            dict с порогами {col: (q1, q99)}
        """
        thresholds = {}
        for col in ['close', 'volume']:
            if col in df.columns:
                q1 = df[col].quantile(0.01)
                q99 = df[col].quantile(0.99)
                thresholds[col] = (q1, q99)
        return thresholds


# ============================================================================
# TRIPLE BARRIER METHOD LABELER
# ============================================================================

class TripleBarrierLabeler:
    """
    ✅ 3 КЛАССА — Triple Barrier Method (TP / Neutral / SL)
    
    Target = 1   если return > +pt_ratio (TP)
    Target = 0   если -sl_ratio <= return <= +pt_ratio (Neutral)
    Target = -1  если return < -sl_ratio (SL)
    
    Это даёт больше информации чем binary!
    """
    @staticmethod
    def get_labels(df: pd.DataFrame, pt_ratio: float = 0.02, sl_ratio: float = 0.01, window: int = 20) -> pd.Series:
        """
        Разметка на 3 класса: TP / Neutral / SL

        Args:
            df: DataFrame с данными
            pt_ratio: TP threshold (например, 0.02 = +2%)
            sl_ratio: SL threshold (например, 0.01 = -1%)
            window: Горизонт в днях

        Returns:
            Series с labels (1 = TP, 0 = Neutral, -1 = SL)
        """
        logger.info(f"Запуск 3-классовой разметки (TP={pt_ratio}, SL={-sl_ratio}, window={window})...")

        labels = pd.Series(index=df.index, data=np.nan)

        # Обрабатываем каждый тикер отдельно
        for ticker, group in df.groupby('Name'):
            prices = group['close'].values
            indices = group.index.values

            for i in range(len(prices) - window):
                start_price = prices[i]
                future_price = prices[i + window]
                
                # ✅ Вычисляем return
                ret = (future_price - start_price) / start_price

                # ✅ 3 класса
                if ret > pt_ratio:
                    labels.at[indices[i]] = 1      # TP
                elif ret < -sl_ratio:
                    labels.at[indices[i]] = -1     # SL
                else:
                    labels.at[indices[i]] = 0      # Neutral

        return labels.fillna(0).astype(int)


# ============================================================================
# PORTFOLIO SIMULATOR
# ============================================================================

class PortfolioSimulator:
    """
    ✅ Полноценный daily portfolio simulator
    
    - per-ticker позиции
    - точный holding period по датам
    - rebalance каждый день
    - лимит открытых позиций
    - long/short учёт
    - slippage + commission
    """
    def __init__(self, initial_capital=100_000, max_positions=10, tb_window=20,
                 commission=0.0005, slippage=0.001, allow_shorts=False):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_positions = max_positions
        self.tb_window = tb_window
        self.cost_per_trade = commission + slippage
        self.allow_shorts = allow_shorts
        self.positions = {}  # ticker: {'shares': float, 'entry_price': float, 'entry_date': pd.Timestamp}
        self.equity_curve = []
        self.trades = []
    
    def run(self, df: pd.DataFrame) -> dict:
        """
        Запуск симуляции
        
        Args:
            df: DataFrame с колонками 'date', 'Name', 'close', 'signal'
        
        Returns:
            dict с метриками
        """
        df = df.sort_values(['date', 'Name']).copy()
        daily_groups = df.groupby('date')
        
        for current_date, day_df in daily_groups:
            day_df = day_df.set_index('Name')
            
            # 1. Закрываем позиции, которым >= TB_WINDOW дней
            to_close = [t for t, pos in list(self.positions.items()) 
                       if (current_date - pos['entry_date']).days >= self.tb_window]
            for ticker in to_close:
                pos = self.positions.pop(ticker)
                exit_price = day_df.loc[ticker, 'close']
                direction = pos.get('direction', 1)  # ✅ Получаем direction
                
                # ✅ Правильный P&L с учётом direction
                if direction == 1:  # Long
                    # Long: купили дешевле, продали дороже
                    cash_in = abs(pos['shares']) * exit_price  # деньги приходят
                    cost = abs(pos['shares']) * exit_price * self.cost_per_trade
                    self.capital += cash_in - cost
                else:  # Short
                    # Short: продали дорого, купили дешевле
                    cash_out = abs(pos['shares']) * exit_price  # деньги уходят на покупку
                    cost = abs(pos['shares']) * exit_price * self.cost_per_trade
                    self.capital -= cash_out + cost
                
                # ✅ Считаем PnL для статистики
                if direction == 1:
                    gross_pnl = pos['shares'] * (exit_price - pos['entry_price'])
                else:
                    gross_pnl = -pos['shares'] * (pos['entry_price'] - exit_price)  # ✅ для short
                
                net_pnl = gross_pnl - (abs(pos['shares']) * exit_price * self.cost_per_trade * 2)  # entry + exit
                self.trades.append({'ticker': ticker, 'pnl': net_pnl, 'bars': self.tb_window, 'direction': direction})
            
            # 2. Новые сигналы
            long_signals = day_df[day_df['signal'] == 1]
            short_signals = day_df[day_df['signal'] == -1] if self.allow_shorts else pd.DataFrame()
            
            avail_slots = self.max_positions - len(self.positions)
            if avail_slots > 0:
                trade_size = self.capital * 0.95 / max(avail_slots, 1)  # 5% резерв
                
                # Long
                for ticker, row in long_signals.iterrows():
                    if len(self.positions) >= self.max_positions: break
                    if ticker not in day_df.index: continue
                    price = row['close']
                    shares = trade_size / price
                    
                    # ✅ Явный direction для long
                    direction = 1
                    cash_out = direction * abs(shares) * price  # long: деньги уходят
                    cost = abs(shares) * price * self.cost_per_trade
                    
                    self.positions[ticker] = {
                        'shares': shares,
                        'entry_price': price,
                        'entry_date': current_date,
                        'direction': direction
                    }
                    self.capital -= cash_out + cost  # ✅ Деньги уходят + commission
                
                # Short (если разрешено)
                if self.allow_shorts:
                    for ticker, row in short_signals.iterrows():
                        if len(self.positions) >= self.max_positions: break
                        if ticker not in day_df.index: continue
                        price = row['close']
                        shares = trade_size / price
                        
                        # ✅ Явный direction для short
                        direction = -1
                        cash_in = abs(shares) * price  # short: деньги приходят (продажа)
                        cost = abs(shares) * price * self.cost_per_trade
                        
                        self.positions[ticker] = {
                            'shares': -shares,  # negative for short
                            'entry_price': price,
                            'entry_date': current_date,
                            'direction': direction
                        }
                        self.capital += cash_in - cost  # ✅ Деньги приходят - commission
            
            # 3. Оценка текущего equity
            port_value = self.capital
            for ticker, pos in self.positions.items():
                if ticker in day_df.index:
                    port_value += pos['shares'] * day_df.loc[ticker, 'close']
            self.equity_curve.append(port_value)
        
        # Финальные метрики
        equity_series = pd.Series(self.equity_curve)
        returns = equity_series.pct_change().dropna()
        
        sharpe = np.sqrt(252) * returns.mean() / (returns.std() + 1e-8) if len(returns) > 0 else 0
        
        # Sortino
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 1e-8
        sortino = np.sqrt(252) * returns.mean() / downside_std if downside_std > 0 else 0
        
        # Max Drawdown
        max_drawdown = ((equity_series / equity_series.cummax()) - 1).min() * 100
        
        # Total Return
        total_return = (equity_series.iloc[-1] / self.initial_capital - 1) * 100
        
        # Win Rate
        if len(self.trades) > 0:
            winning_trades = [t for t in self.trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(self.trades)
        else:
            win_rate = 0
        
        return {
            'sharpe': sharpe,
            'sortino': sortino,
            'max_drawdown': max_drawdown,
            'total_return': total_return,
            'trades': len(self.trades),
            'win_rate': win_rate,
            'equity_curve': equity_series
        }


# ============================================================================
# MULTICLASS SIGNAL MAPPER
# ============================================================================
class MulticlassSignalMapper:
    """
    Надёжная обёртка для multiclass моделей с перемапленными метками
    Поддерживает как оригинальные классы [-1,0,1], так и mapped [0,1,2]
    """

    def __init__(self):
        self.class_to_idx = None
        self.tp_idx = None  # индекс класса TP (long)
        self.sl_idx = None  # индекс класса SL (short)
        self.neutral_idx = None  # индекс класса Neutral (flat)

    def fit(self, model):
        """Фиксируем порядок классов после обучения"""
        classes = model.classes_
        self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}

        # Поддержка двух вариантов меток
        if -1 in self.class_to_idx and 1 in self.class_to_idx:
            # Оригинальные метки [-1, 0, 1]
            self.sl_idx = self.class_to_idx.get(-1)
            self.neutral_idx = self.class_to_idx.get(0)
            self.tp_idx = self.class_to_idx.get(1)
        else:
            # Mapped метки [0, 1, 2] → SL, Neutral, TP
            self.sl_idx = self.class_to_idx.get(0)
            self.neutral_idx = self.class_to_idx.get(1)
            self.tp_idx = self.class_to_idx.get(2)

        logger.info(f"✅ Классы зафиксированы: {classes} → "
                    f"SL={self.sl_idx}, Neutral={self.neutral_idx}, TP={self.tp_idx}")
        return self

    def predict_signal(self, proba: np.ndarray, conf_threshold: float = 0.55) -> np.ndarray:
        """
        Возвращает сигналы -1/0/1
        """
        n_samples = len(proba)
        signals = np.zeros(n_samples, dtype=int)  # по умолчанию flat (0)

        # Long (TP)
        if self.tp_idx is not None:
            tp_conf = proba[:, self.tp_idx]
            if self.sl_idx is not None:
                is_long = (tp_conf > conf_threshold) & (tp_conf > proba[:, self.sl_idx])
            else:
                is_long = tp_conf > conf_threshold
            signals = np.where(is_long, 1, signals)

        # Short (SL)
        if self.sl_idx is not None:
            sl_conf = proba[:, self.sl_idx]
            if self.tp_idx is not None:
                is_short = (sl_conf > conf_threshold) & (sl_conf > proba[:, self.tp_idx])
            else:
                is_short = sl_conf > conf_threshold
            signals = np.where(is_short, -1, signals)

        return signals


class FeaturePipeline:
    """
    Единый пайплайн для всех признаков
    
    Преимущества:
    - Нет дублирования между train и predict
    - Гарантированно одинаковые признаки
    - Можно сохранить/загрузить
    """
    
    def __init__(self, max_features: int = 100):
        self.max_features = max_features
        self.feature_columns = []
        self.fitted = False
        # StandardScaler НЕ нужен для деревьев!
        self.feature_selector = None
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание всех признаков"""
        logger.info("Создание признаков...")
        
        df = df.copy()
        
        # 1. Скользящие средние
        df = self._create_moving_averages(df)
        
        # 2. Momentum
        df = self._create_momentum_features(df)
        
        # 3. Волатильность
        df = self._create_volatility_features(df)
        
        # 4. Объём
        df = self._create_volume_features(df)
        
        # 5. Lag признаки
        df = self._create_lag_features(df)
        
        # 6. Rolling статистики
        df = self._create_rolling_features(df)
        
        # 7. Паттерны
        df = self._create_pattern_features(df)
        
        # 8. Сезонность
        df = self._create_seasonal_features(df)
        
        # 9. Макро (если есть)
        if any(col in df.columns for col in ['key_rate', 'usd_rub', 'oil_price']):
            df = self._create_macro_features(df)
        
        # Сохраняем список признаков
        exclude_cols = ['date', 'Name', 'open', 'high', 'low', 'close', 'volume', 
                       'target_7d', 'target_30d', 'target_90d']
        self.feature_columns = [col for col in df.columns 
                               if col not in exclude_cols 
                               and not col.startswith('Unnamed')
                               and df[col].dtype in [np.float64, np.int64, np.float32, np.int32]]
        
        logger.info(f"Создано {len(self.feature_columns)} признаков")
        
        return df
    
    def _create_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Скользящие средние"""
        for window in [5, 10, 20, 50, 200]:
            df[f'ma_{window}'] = df['close'].rolling(window).mean()
            df[f'ma_{window}_ratio'] = df['close'] / (df[f'ma_{window}'] + 1e-8)
        
        # EMA
        for span in [12, 26]:
            df[f'ema_{span}'] = df['close'].ewm(span=span).mean()
        
        return df
    
    def _create_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Momentum индикаторы"""
        # ✅ Log Returns вместо pct_change (аддитивны, более нормальное распределение)
        logger.debug("   Создаём Log Returns для momentum...")
        
        # ✅ Log Returns (аддитивны!)
        for period in [1, 3, 5, 10, 20, 60]:
            df[f'log_return_{period}d'] = np.log(df['close'] / df['close'].shift(period))
        
        # ✅ Простые returns оставляем для интерпретации
        for period in [1, 3, 5, 10, 20, 60]:
            df[f'return_{period}d'] = df['close'].pct_change(period)

        # RSI (на log returns)
        delta = df['log_return_1d'] if 'log_return_1d' in df.columns else df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-8)
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # RSI для других периодов
        for period in [7, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / (loss + 1e-8)
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # ROC (Rate of Change)
        for period in [10, 20]:
            df[f'roc_{period}'] = (df['close'] - df['close'].shift(period)) / (df['close'].shift(period) + 1e-8) * 100

        return df
    
    def _create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Волатильность"""
        # Стандартная волатильность
        for window in [5, 10, 20, 60]:
            df[f'volatility_{window}d'] = df['close'].pct_change().rolling(window).std()
        
        # ATR (Average True Range)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        for window in [14, 20]:
            df[f'atr_{window}'] = df['true_range'].rolling(window).mean()
        
        df['atr_ratio'] = df['atr_14'] / (df['close'] + 1e-8)
        
        # Parkinson Volatility
        df['parkinson'] = (
            1 / (4 * np.log(2)) * 
            (np.log(df['high'] / df['low']) ** 2)
        ).rolling(20).mean()
        
        # Garman-Klass Volatility
        log_hl = np.log(df['high'] / df['low'])
        log_co = np.log(df['close'] / df['open'])
        df['garman_klass'] = (
            0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2
        ).rolling(20).mean()
        
        return df
    
    def _create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Объёмные индикаторы"""
        # Volume MA
        for window in [5, 10, 20]:
            df[f'volume_ma_{window}'] = df['volume'].rolling(window).mean()
        
        df['volume_ratio'] = df['volume'] / (df['volume_ma_20'] + 1e-8)
        
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        
        df['vwap'] = (df['close'] * df['volume']).cumsum() / (df['volume'].cumsum() + 1e-8)
        df['vwap_ratio'] = df['close'] / (df['vwap'] + 1e-8)
        
        # MFI (Money Flow Index approximation)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        delta = typical_price.diff()
        positive_flow = money_flow.where(delta > 0, 0)
        negative_flow = money_flow.where(delta < 0, 0)
        
        positive_mf = positive_flow.rolling(14).sum()
        negative_mf = negative_flow.rolling(14).sum()
        
        df['mfi'] = 100 - (100 / (1 + positive_mf / (negative_mf + 1e-8)))
        
        return df
    
    def _create_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Lag признаки"""
        # ✅ Используем Log Returns для стационарности!
        # ❌ close_lag нестационарен (цены растут со временем)
        # ✅ log_return_lag стационарен
        logger.debug("   Создаём lag признаки на log returns...")
        
        for lag in [1, 2, 3, 5, 10, 20]:
            # ✅ Log return lag (стационарно)
            if 'log_return_1d' in df.columns:
                df[f'log_return_lag_{lag}'] = df['log_return_1d'].shift(lag)
            
            # ✅ Return lag (стационарно)
            if 'return_1d' in df.columns:
                df[f'return_lag_{lag}'] = df['return_1d'].shift(lag)
            
            # ✅ Volume lag (относительный, стационарно)
            if 'volume_ma_20' in df.columns:
                df[f'volume_lag_{lag}'] = (df['volume'] / df['volume_ma_20']).shift(lag)
            else:
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            
            # ✅ RSI lag (уже стационарен, 0-100)
            df[f'rsi_lag_{lag}'] = df['rsi_14'].shift(lag) if 'rsi_14' in df.columns else 50

        return df
    
    def _create_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rolling статистики"""
        # ✅ Используем относительные величины для стационарности!
        logger.debug("   Создаём rolling признаки (относительные)...")
        
        for window in [5, 10, 20]:
            # ✅ Log return mean/std (стационарно)
            if 'log_return_1d' in df.columns:
                df[f'log_return_mean_{window}'] = df['log_return_1d'].rolling(window).mean()
                df[f'log_return_std_{window}'] = df['log_return_1d'].rolling(window).std()
            
            # ✅ Close / MA (стационарно, отношение)
            df[f'close_mean_{window}'] = df['close'].rolling(window).mean()
            df[f'close_to_ma_{window}'] = df['close'] / (df[f'close_mean_{window}'] + 1e-8)

            # Min/Max
            df[f'close_min_{window}'] = df['close'].rolling(window).min()
            df[f'close_max_{window}'] = df['close'].rolling(window).max()

            # ✅ Позиция цены в диапазоне (стационарно, 0-1)
            df[f'close_position_{window}'] = (
                (df['close'] - df[f'close_min_{window}']) /
                (df[f'close_max_{window}'] - df[f'close_min_{window}'] + 1e-8)
            )

            # ✅ Skew и Kurtosis на log returns (стационарно)
            if 'log_return_1d' in df.columns:
                df[f'log_return_skew_{window}'] = df['log_return_1d'].rolling(window).skew()
                df[f'log_return_kurt_{window}'] = df['log_return_1d'].rolling(window).kurt()

        return df
    
    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Паттерны свечей"""
        # Размер свечи
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_range'] = df['high'] - df['low']
        df['candle_ratio'] = df['candle_body'] / (df['candle_range'] + 1e-8)
        
        # Верхние и нижние тени
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        
        # Бычьи/медвежьи паттерны
        df['bullish'] = (df['close'] > df['open']).astype(int)
        df['bearish'] = (df['close'] < df['open']).astype(int)
        
        # Doji
        df['is_doji'] = (df['candle_ratio'] < 0.1).astype(int)
        
        # Режим рынка
        df['ma50_above_ma200'] = (df['ma_50'] > df['ma_200']).astype(int) if 'ma_50' in df.columns else 0
        df['price_above_ma200'] = (df['close'] > df['ma_200']).astype(int) if 'ma_200' in df.columns else 0
        df['price_above_ma50'] = (df['close'] > df['ma_50']).astype(int) if 'ma_50' in df.columns else 0
        
        # Золотой крест / Крест смерти
        if 'ma_50' in df.columns and 'ma_200' in df.columns:
            df['golden_cross'] = ((df['ma_50'] > df['ma_200']) & 
                                  (df['ma_50'].shift(1) <= df['ma_200'].shift(1))).astype(int)
            df['death_cross'] = ((df['ma_50'] < df['ma_200']) & 
                                 (df['ma_50'].shift(1) >= df['ma_200'].shift(1))).astype(int)
        
        return df
    
    def _create_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Сезонность"""
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_month'] = df['date'].dt.day
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        
        # Is month start/end
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
        
        # Циклические признаки
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 31)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 31)
        
        return df
    
    def _create_macro_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Макро признаки"""
        macro_cols = ['key_rate', 'usd_rub', 'oil_price', 'inflation']
        
        for col in macro_cols:
            if col in df.columns:
                # Lag
                df[f'{col}_lag1'] = df[col].shift(1)
                df[f'{col}_lag7'] = df[col].shift(7)
                
                # Изменение
                df[f'{col}_change'] = df[col].diff()
                df[f'{col}_change_pct'] = df[col].pct_change() * 100
                
                # Скользящее среднее
                df[f'{col}_ma30'] = df[col].rolling(30).mean()
        
        # Спреды
        if 'key_rate' in df.columns and 'inflation' in df.columns:
            df['real_rate'] = df['key_rate'] - df['inflation']
        
        return df
    
    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """Обучение пайплайна"""
        logger.info("Обучение FeaturePipeline...")

        # ❌ StandardScaler НЕ нужен для деревьев!
        # X_scaled = self.scaler.fit_transform(X)
        # Просто используем X как есть

        # Feature Selection — ОТКЛЮЧАЕМ
        self.feature_selector = None  # Отключено!

        self.fitted = True
        logger.info(f"FeaturePipeline обучен ({len(self.feature_columns)} признаков)")

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Трансформация данных"""
        if not self.fitted:
            raise ValueError("Сначала вызовите fit()")

        # Выбор признаков
        X_selected = X[self.feature_columns]

        # ❌ StandardScaler НЕ нужен — возвращаем как есть
        return X_selected
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series = None) -> np.ndarray:
        """Обучение и трансформация"""
        self.fit(X, y)
        return self.transform(X)
    
    def get_feature_names(self) -> List[str]:
        """Получить имена признаков после селекции"""
        if self.feature_selector is not None:
            mask = self.feature_selector.get_support()
            return [feat for feat, keep in zip(self.feature_columns, mask) if keep]
        return self.feature_columns


# ============================================================================
# PURGED TIME SERIES CV
# ============================================================================

class PurgedTimeSeriesSplit:
    """
    ✅ Purged TimeSeries Split с gap ПО ДАТАМ + group-aware
    Защита от leakage через overlapping targets И через тикеры
    
    ✅ ВАЖНО: Данные должны быть отсортированы ПО ДАТЕ перед использованием!
    """

    def __init__(self, n_splits: int = 5, gap_days: int = 30):
        self.n_splits = n_splits
        self.gap_days = gap_days

    def split(self, X: pd.DataFrame, y: pd.Series = None, groups=None):
        """Генерация индексов для CV С PURGE ПО ДАТАМ
        
        ✅ Данные должны быть отсортированы по дате (global sort)!
        ✅ Каждый split содержит ВСЕ тикеры в этот период (нет leakage через тикеры)
        """
        n_samples = len(X)

        # ✅ Данные уже отсортированы по дате (global sort по всем тикерам)
        # Просто используем порядковые индексы
        sorted_indices = np.arange(n_samples)
        
        # ✅ Вычисляем gap в индексах на основе дней
        if 'date' in X.columns:
            dates = pd.to_datetime(X['date'])
            date_range = (dates.max() - dates.min()).days
            samples_per_day = n_samples / max(date_range, 1)
            gap_indices = int(self.gap_days * samples_per_day)
        else:
            gap_indices = self.gap_days

        # Минимальный размер фолда
        min_test_size = n_samples // (self.n_splits + 1)

        for i in range(self.n_splits):
            # Train end
            train_end_idx = (i + 1) * min_test_size

            # ✅ Gap (purge) между train и test
            gap_end_idx = train_end_idx + gap_indices

            # Test start и end
            test_start_idx = gap_end_idx
            test_end_idx = test_start_idx + min_test_size

            if test_end_idx >= n_samples:
                break

            # ✅ Используем прямые индексы (данные уже отсортированы!)
            # ✅ Каждый split содержит ВСЕ тикеры в этот период
            train_indices = sorted_indices[:train_end_idx]
            test_indices = sorted_indices[test_start_idx:test_end_idx]

            yield train_indices, test_indices

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        return self.n_splits


# ============================================================================
# OPTUNA HYPERPARAMETER OPTIMIZATION
# ============================================================================

class HyperparameterOptimizer:
    """Оптимизация гиперпараметров с Optuna"""
    
    def __init__(self, n_trials: int = 50, timeout: int = 3600):  # УМЕНЬШЕНО со 100/14400
        self.n_trials = n_trials
        self.timeout = timeout
        self.best_params = None
    
    def optimize(self, X_train, y_train, X_val, y_val, model_type: str = 'xgboost', scale_pos_weight: float = 1.0):
        """Оптимизация гиперпараметров с внутренней кросс-валидацией"""
        try:
            import optuna
            from sklearn.model_selection import cross_val_score, TimeSeriesSplit
        except ImportError:
            logger.warning("Optuna не установлена. Используем параметры по умолчанию.")
            return self._get_default_params(model_type)
        
        def objective(trial):
            # Расширенные параметры для максимального качества
            if model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),  # Расширено
                    'max_depth': trial.suggest_int('max_depth', 3, 8),  # Расширено
                    'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.2, log=True),  # Расширено
                    'subsample': trial.suggest_float('subsample', 0.6, 0.95),  # Расширено
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.95),  # Расширено
                    'min_child_weight': trial.suggest_int('min_child_weight', 3, 20),  # Расширено
                    'gamma': trial.suggest_float('gamma', 0.05, 0.5),  # Расширено
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.05, 10.0, log=True),  # Расширено
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 10.0, log=True),  # Расширено
                    'random_state': 42,
                    'n_jobs': -1,
                    'eval_metric': 'auc',
                    'verbosity': 0,
                    'scale_pos_weight': scale_pos_weight  # ✅ Балансировка классов
                }
                
                try:
                    import xgboost as xgb
                    from sklearn.model_selection import TimeSeriesSplit
                    from sklearn.metrics import roc_auc_score

                    model = xgb.XGBClassifier(**params)

                    # ✅ PurgedTimeSeriesSplit для time series (с gap!)
                    tscv = PurgedTimeSeriesSplit(n_splits=3, gap_days=Config.TB_WINDOW)
                    manual_scores = []

                    for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(X_train)):
                        # ✅ X_train — DataFrame, используем .iloc
                        X_tr_fold = X_train.iloc[train_idx]
                        y_tr_fold = y_train.iloc[train_idx]
                        X_te_fold = X_train.iloc[test_idx]
                        y_te_fold = y_train.iloc[test_idx]

                        # Проверка баланса в fold'ах
                        if len(np.unique(y_tr_fold)) < 2 or len(np.unique(y_te_fold)) < 2:
                            logger.debug(f"Trial {trial.number}, Fold {fold_idx}: только один класс!")
                            manual_scores.append(np.nan)
                            continue

                        # Быстрое обучение
                        model_fold = xgb.XGBClassifier(**params)
                        model_fold.fit(X_tr_fold, y_tr_fold, verbose=False)

                        # Предсказание
                        y_pred_proba = model_fold.predict_proba(X_te_fold)[:, 1]

                        # Проверка
                        if len(np.unique(y_pred_proba)) < 2:
                            logger.debug(f"Trial {trial.number}, Fold {fold_idx}: модель предсказывает одно значение!")
                            manual_scores.append(np.nan)
                            continue

                        score = roc_auc_score(y_te_fold, y_pred_proba)
                        logger.debug(f"Trial {trial.number}, Fold {fold_idx}: AUC = {score:.4f}")
                        manual_scores.append(score)

                    scores = np.array(manual_scores)
                    logger.debug(f"Trial {trial.number}: TimeSeries CV scores = {scores}, mean = {np.nanmean(scores):.4f}")

                    # ✅ Оптимизируем по ROC-AUC (честно для classification!)
                    # Sharpe будет считаться в backtest
                    score = np.nanmean(scores)

                    # Проверка на NaN
                    if np.isnan(score) or np.isinf(score):
                        logger.warning(f"Trial {trial.number}: score={score}, заменяем на 0.5")
                        return 0.5

                    return score
                except Exception as e:
                    logger.warning(f"Trial {trial.number} failed: {e}")
                    import traceback
                    logger.warning(traceback.format_exc())
                    return 0.5
            
            elif model_type == 'lightgbm':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 200, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 8),
                    'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.1, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 0.9),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.9),
                    'min_child_samples': trial.suggest_int('min_child_samples', 10, 50),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.1, 10.0, log=True),
                    'reg_lambda': trial.suggest_float('reg_lambda', 1.0, 10.0, log=True),
                    'random_state': 42,
                    'verbose': -1,
                    'n_jobs': -1
                }
                
                try:
                    import lightgbm as lgb
                    model = lgb.LGBMClassifier(**params)
                    model.fit(X_train, y_train)
                    y_pred_proba = model.predict_proba(X_val)[:, 1]
                    score = roc_auc_score(y_val, y_pred_proba)
                except:
                    return 0.5
            
            else:  # catboost
                params = {
                    'iterations': trial.suggest_int('iterations', 200, 1000),
                    'depth': trial.suggest_int('depth', 3, 8),
                    'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.1, log=True),
                    'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0, log=True),
                    'random_seed': 42,
                    'verbose': 0,
                    'thread_count': -1
                }
                
                try:
                    from catboost import CatBoostClassifier
                    model = CatBoostClassifier(**params)
                    model.fit(X_train, y_train, verbose=False)
                    y_pred_proba = model.predict_proba(X_val)[:, 1]
                    score = roc_auc_score(y_val, y_pred_proba)
                except:
                    return 0.5
            
            return score
        
        logger.info(f"Запуск оптимизации Optuna ({self.n_trials} итераций)...")
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)
        
        self.best_params = study.best_params
        logger.info(f"Лучшие параметры: {self.best_params}")
        logger.info(f"Лучший ROC-AUC: {study.best_value:.4f}")
        
        return self.best_params
    
    def _get_default_params(self, model_type: str) -> Dict:
        """Параметры по умолчанию"""
        if model_type == 'xgboost':
            return {
                'n_estimators': 500,
                'max_depth': 5,
                'learning_rate': 0.01,
                'subsample': 0.7,
                'colsample_bytree': 0.7,
                'min_child_weight': 10,
                'gamma': 0.2,
                'reg_alpha': 1.0,
                'reg_lambda': 5.0,
                'random_state': 42,
                'n_jobs': -1
            }
        elif model_type == 'lightgbm':
            return {
                'n_estimators': 500,
                'max_depth': 5,
                'learning_rate': 0.01,
                'subsample': 0.7,
                'colsample_bytree': 0.7,
                'min_child_samples': 20,
                'reg_alpha': 1.0,
                'reg_lambda': 5.0,
                'random_state': 42,
                'n_jobs': -1
            }
        else:  # catboost
            return {
                'iterations': 500,
                'depth': 5,
                'learning_rate': 0.01,
                'l2_leaf_reg': 5.0,
                'random_seed': 42,
                'verbose': 0,
                'thread_count': -1
            }

    def optimize_multiclass(self, X_train, y_train, X_val, y_val, model_type: str = 'xgboost'):
        """Оптимизация для multiclass классификации (3 класса)"""
        try:
            import optuna
        except ImportError:
            logger.warning("Optuna не установлена")
            return self._get_default_params_multiclass(model_type)

        def objective(trial):
            if model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 8),
                    'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.2, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 0.95),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.95),
                    'min_child_weight': trial.suggest_int('min_child_weight', 3, 20),
                    'gamma': trial.suggest_float('gamma', 0.05, 0.5),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.05, 10.0, log=True),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 10.0, log=True),
                    'random_state': 42,
                    'n_jobs': -1,
                    'eval_metric': 'mlogloss',
                    'verbosity': 0
                }

                try:
                    import xgboost as xgb
                    
                    # ✅ PurgedTimeSeriesSplit вместо обычного TimeSeriesSplit
                    tscv = PurgedTimeSeriesSplit(n_splits=3, gap_days=30)
                    scores = []

                    for train_idx, test_idx in tscv.split(X_train):
                        X_tr = X_train.iloc[train_idx]
                        y_tr = y_train.iloc[train_idx]
                        X_te = X_train.iloc[test_idx]
                        y_te = y_train.iloc[test_idx]
                        
                        model_fold = xgb.XGBClassifier(
                            **params,
                            objective='multi:softprob',
                            num_class=3
                        )
                        model_fold.fit(X_tr, y_tr, verbose=False)
                        y_pred_proba = model_fold.predict_proba(X_te)
                        score = roc_auc_score(y_te, y_pred_proba, multi_class='ovr', average='macro')
                        scores.append(score)
                    
                    return np.mean(scores)
                except Exception as e:
                    logger.warning(f"Trial failed: {e}")
                    return 0.5

            return 0.5

        logger.info(f"Запуск Optuna multiclass ({self.n_trials} итераций)...")
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)

        best_params = study.best_params
        logger.info(f"Лучшие параметры: {best_params}")
        logger.info(f"Лучший ROC-AUC (multiclass): {study.best_value:.4f}")

        return best_params

    def _get_default_params_multiclass(self, model_type: str) -> Dict:
        """Параметры по умолчанию для multiclass"""
        if model_type == 'xgboost':
            return {
                'n_estimators': 500, 'max_depth': 5, 'learning_rate': 0.01,
                'subsample': 0.7, 'colsample_bytree': 0.7, 'min_child_weight': 10,
                'gamma': 0.2, 'reg_alpha': 1.0, 'reg_lambda': 5.0,
                'random_state': 42, 'n_jobs': -1
            }
        return {}


# ============================================================================
# МОДЕЛЬ
# ============================================================================

class UltimateEnsembleModelV4:
    """Продвинутый ансамбль v4.0"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.models = {}  # По одному на горизонт
        self.feature_pipelines = {}
        self.metrics = {}
        self.feature_importance = {}

    def _ensemble_predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Weighted ensemble предсказание (нужен для pickle)"""
        if not hasattr(self, '_estimators') or not hasattr(self, '_weights'):
            raise RuntimeError("Сначала нужно обучить модель (вызвать fit())")

        base_preds = np.zeros((len(X), 3), dtype=np.float32)
        for (name, model), w in zip(self._estimators, self._weights):
            base_preds += w * model.predict_proba(X)
        return base_preds
    
    def fit(self, data: pd.DataFrame, optimize_hyperparams: bool = True):
        """Обучение модели"""
        logger.info("=" * 80)
        logger.info("INVESTEDU ML MODEL v4.0 — ОБУЧЕНИЕ")
        logger.info("=" * 80)
        
        # 1. Валидация данных
        logger.info("\n1. ВАЛИДАЦИЯ ДАННЫХ")
        is_valid, errors, warnings = DataValidator.validate(data)
        
        if not is_valid:
            logger.error(f"Валидация не пройдена: {errors}")
            raise ValueError(f"Валидация данных не пройдена: {errors}")
        
        for warning in warnings:
            logger.warning(warning)
        
        # 2. Очистка данных
        logger.info("\n2. ОЧИСТКА ДАННЫХ")
        
        # ✅ РАЗДЕЛЯЕМ на train/val/test ДО winsorization
        # Чтобы избежать leakage через пороги
        full_raw = data[['date', 'Name', 'open', 'high', 'low', 'close', 'volume']].copy()
        full_raw['date'] = pd.to_datetime(full_raw['date'])
        
        train_raw = full_raw[full_raw['date'].dt.year < self.config.TRAIN_END_YEAR].copy()
        val_raw = full_raw[
            (full_raw['date'].dt.year >= self.config.TRAIN_END_YEAR) &
            (full_raw['date'].dt.year < self.config.TEST_START_YEAR)
        ].copy()
        test_raw = full_raw[full_raw['date'].dt.year >= self.config.TEST_START_YEAR].copy()
        
        # ✅ Вычисляем пороги winsorization ТОЛЬКО на train
        quantile_thresholds = DataValidator.compute_winsorization_thresholds(train_raw)

        # ✅ Применяем пороги ко всем сетам
        train_raw = DataValidator.clean(train_raw, quantile_thresholds=quantile_thresholds)
        val_raw = DataValidator.clean(val_raw, quantile_thresholds=quantile_thresholds)
        test_raw = DataValidator.clean(test_raw, quantile_thresholds=quantile_thresholds)

        logger.info(f"Train после очистки: {len(train_raw):,} строк")
        logger.info(f"Val после очистки: {len(val_raw):,} строк")
        logger.info(f"Test после очистки: {len(test_raw):,} строк")
        
        # ✅ Добавляем макро данные к train/val/test (уже после очистки!)
        # Макро уже есть в data (из merge_data), просто копируем
        for col in ['key_rate', 'usd_rub', 'oil_price', 'inflation']:
            if col in data.columns:
                # ✅ Merge по дате и Name (правильный alignment!)
                train_raw = train_raw.merge(data[['date', 'Name', col]].drop_duplicates(), 
                                           on=['date', 'Name'], how='left')
                val_raw = val_raw.merge(data[['date', 'Name', col]].drop_duplicates(), 
                                       on=['date', 'Name'], how='left')
                test_raw = test_raw.merge(data[['date', 'Name', col]].drop_duplicates(), 
                                         on=['date', 'Name'], how='left')
        
        # 3. Feature Engineering — ТЕПЕРЬ ПОСЛЕ split!
        logger.info("\n3. FEATURE ENGINEERING (ПОСЛЕ split, нет leakage)")
        feature_pipeline = FeaturePipeline(max_features=self.config.MAX_FEATURES)

        # ✅ ТЕПЕРЬ создаём признаки ОТДЕЛЬНО для каждого сета!
        # Это предотвращает leakage через rolling/ewm/lag
        logger.info("\n   ✅ Создание признаков для train...")
        train_features_list = []
        for name, group in train_raw.groupby('Name'):
            group_features = feature_pipeline.create_all_features(group.copy())
            train_features_list.append(group_features)
        train_df = pd.concat(train_features_list, ignore_index=True)

        logger.info("   ✅ Создание признаков для val...")
        val_features_list = []
        for name, group in val_raw.groupby('Name'):
            group_features = feature_pipeline.create_all_features(group.copy())
            val_features_list.append(group_features)
        val_df = pd.concat(val_features_list, ignore_index=True)

        logger.info("   ✅ Создание признаков для test...")
        test_features_list = []
        for name, group in test_raw.groupby('Name'):
            group_features = feature_pipeline.create_all_features(group.copy())
            test_features_list.append(group_features)
        test_df = pd.concat(test_features_list, ignore_index=True)

        # ✅ ГЛОБАЛЬНАЯ СОРТИРОВКА ПО ДАТЕ (критично для PurgedTimeSeriesSplit!)
        logger.info("   ✅ Глобальная сортировка по дате...")
        train_df = train_df.sort_values(['date', 'Name']).reset_index(drop=True)
        val_df = val_df.sort_values(['date', 'Name']).reset_index(drop=True)
        test_df = test_df.sort_values(['date', 'Name']).reset_index(drop=True)

        logger.info(f"   Train: {len(train_df):,} строк, {len(feature_pipeline.feature_columns)} признаков")
        logger.info(f"   Val: {len(val_df):,} строк")
        logger.info(f"   Test: {len(test_df):,} строк")
        
        # ✅ NaN-ОБРАБОТКА ПОСЛЕ создания признаков!
        logger.info("\n   ✅ NaN-обработка после features...")
        
        # Missing indicators для макро
        for col in ['key_rate', 'usd_rub', 'oil_price', 'inflation']:
            if col in train_df.columns:
                train_df[f'{col}_is_missing'] = train_df[col].isnull().astype(int)
                val_df[f'{col}_is_missing'] = val_df[col].isnull().astype(int)
                test_df[f'{col}_is_missing'] = test_df[col].isnull().astype(int)
        
        # ✅ WARMUP — удаляем первые 20 дней для каждого тикера (вместо 200 для сохранения данных)
        logger.info("   ✅ WARMUP — удаление первых 20 дней...")
        train_df = train_df.groupby('Name').apply(lambda x: x.iloc[20:]).reset_index(drop=True)
        val_df = val_df.groupby('Name').apply(lambda x: x.iloc[20:]).reset_index(drop=True)
        test_df = test_df.groupby('Name').apply(lambda x: x.iloc[20:]).reset_index(drop=True)
        
        # ✅ ГЛОБАЛЬНАЯ СОРТИРОВКА ПОСЛЕ WARMUP!
        train_df = train_df.sort_values(['date', 'Name']).reset_index(drop=True)
        val_df = val_df.sort_values(['date', 'Name']).reset_index(drop=True)
        test_df = test_df.sort_values(['date', 'Name']).reset_index(drop=True)
        
        logger.info(f"   Train после warmup: {len(train_df):,} строк")
        
        # ✅ Контроль NaN — удаляем признаки с >50% NaN в train
        nan_ratio = train_df[feature_pipeline.feature_columns].isnull().mean()
        bad_features = nan_ratio[nan_ratio > 0.5].index.tolist()
        if len(bad_features) > 0:
            logger.info(f"   Удаляем {len(bad_features)} признаков с >50% NaN")
            feature_pipeline.feature_columns = [c for c in feature_pipeline.feature_columns if c not in bad_features]
        
        # ✅ Добавляем missing indicators для всех признаков с NaN
        features_with_nan = nan_ratio[nan_ratio > 0].index.tolist()
        for col in features_with_nan:
            if col in feature_pipeline.feature_columns:
                train_df[f'{col}_is_missing'] = train_df[col].isnull().astype(int)
                val_df[f'{col}_is_missing'] = val_df[col].isnull().astype(int)
                test_df[f'{col}_is_missing'] = test_df[col].isnull().astype(int)
        
        logger.info(f"   Добавлено {len(features_with_nan)} missing indicators")
        
        # ✅ Заполняем оставшиеся NaN медианой из train
        for col in feature_pipeline.feature_columns:
            if col in train_df.columns:
                median_val = train_df[col].median()
                train_df[col] = train_df[col].fillna(median_val)
                val_df[col] = val_df[col].fillna(median_val)
                test_df[col] = test_df[col].fillna(median_val)
        
        logger.info("   ✅ Все NaN обработаны")
        
        # 4. Target — ТОЛЬКО ПОСЛЕ split и features!
        logger.info("\n4. СОЗДАНИЕ TARGET (Triple Barrier — 3 класса)")
        
        # ✅ Triple Barrier Method (3 класса: TP / Neutral / SL)
        logger.info("   ✅ Triple Barrier Method для target (3 класса)")

        # ✅ Параметры из конфига
        PT_RATIO = Config.TB_PT_RATIO  # +2% для TP
        SL_RATIO = Config.TB_SL_RATIO  # -1% для SL
        TB_WINDOW = Config.TB_WINDOW   # 20 дней

        # ✅ Применяем Triple Barrier для train/val/test
        logger.info("   Применяем Triple Barrier для train...")
        train_df['target'] = TripleBarrierLabeler.get_labels(train_df, PT_RATIO, SL_RATIO, TB_WINDOW)
        
        logger.info("   Применяем Triple Barrier для val...")
        val_df['target'] = TripleBarrierLabeler.get_labels(val_df, PT_RATIO, SL_RATIO, TB_WINDOW)
        
        logger.info("   Применяем Triple Barrier для test...")
        test_df['target'] = TripleBarrierLabeler.get_labels(test_df, PT_RATIO, SL_RATIO, TB_WINDOW)

        # ✅ Проверяем баланс 3 классов
        logger.info(f"   Train баланс классов:")
        for cls in [-1, 0, 1]:
            count = (train_df['target'] == cls).sum()
            pct = count / len(train_df) * 100
            logger.info(f"      Класс {cls}: {count:,} ({pct:.1f}%)")
        
        logger.info(f"   Val баланс классов:")
        for cls in [-1, 0, 1]:
            count = (val_df['target'] == cls).sum()
            pct = count / len(val_df) * 100
            logger.info(f"      Класс {cls}: {count:,} ({pct:.1f}%)")
        
        logger.info(f"   Test баланс классов:")
        for cls in [-1, 0, 1]:
            count = (test_df['target'] == cls).sum()
            pct = count / len(test_df) * 100
            logger.info(f"      Класс {cls}: {count:,} ({pct:.1f}%)")
        
        # ✅ Drop последних TB_WINDOW строк
        logger.info(f"\n   ✅ Drop последних {Config.TB_WINDOW} строк (target не определён)")

        def drop_last_window_safe(df, window):
            """Безопасное удаление — только если данных > window"""
            result = []
            for name, group in df.groupby('Name'):
                if len(group) > window:
                    result.append(group.iloc[:-window])
            if result:
                return pd.concat(result, ignore_index=True)
            return df  # Возвращаем оригинал если ничего не осталось

        train_df = drop_last_window_safe(train_df, Config.TB_WINDOW)
        val_df = drop_last_window_safe(val_df, Config.TB_WINDOW)
        test_df = drop_last_window_safe(test_df, Config.TB_WINDOW)
        
        # ✅ ГЛОБАЛЬНАЯ СОРТИРОВКА ПОСЛЕ DROP!
        train_df = train_df.sort_values(['date', 'Name']).reset_index(drop=True)
        val_df = val_df.sort_values(['date', 'Name']).reset_index(drop=True)
        test_df = test_df.sort_values(['date', 'Name']).reset_index(drop=True)

        logger.info(f"   Train после drop: {len(train_df):,} строк")
        logger.info(f"   Val после drop: {len(val_df):,} строк")
        logger.info(f"   Test после drop: {len(test_df):,} строк")
        
        # ✅ Feature correlation filtering (на train)
        logger.info("\n   ✅ Feature correlation filtering...")
        corr_matrix = train_df[feature_pipeline.feature_columns].corr(min_periods=1).abs()
        
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
        
        if len(to_drop) > 0:
            logger.info(f"   Удаляем {len(to_drop)} коррелирующих признаков: {to_drop[:5]}...")
            feature_pipeline.feature_columns = [c for c in feature_pipeline.feature_columns if c not in to_drop]
            logger.info(f"   Осталось признаков: {len(feature_pipeline.feature_columns)}")
        else:
            logger.info("   Нет высококоррелирующих признаков")
        
        # 6. Обучение ОДНОЙ модели (target ОДИН от Triple Barrier!)
        logger.info(f"\n{'=' * 80}")
        logger.info("ОБУЧЕНИЕ МОДЕЛИ (ОДИН target от Triple Barrier)")
        logger.info(f"{'=' * 80}")
        
        # ✅ Используем ОДИН target (не target_{horizon}d!)
        target_col = 'target'  # ✅ ОДИН target для всех

        # ✅ Подготовка X, y
        X_train = train_df[feature_pipeline.feature_columns]
        y_train_raw = train_df[target_col]  # ✅ Сохраняем оригинал (-1, 0, 1)
        X_val = val_df[feature_pipeline.feature_columns]
        y_val_raw = val_df[target_col]
        X_test = test_df[feature_pipeline.feature_columns]
        y_test_raw = test_df[target_col]

        # ✅ МАППИНГ МЕТОК для multiclass (-1→0, 0→1, 1→2)
        # XGBoost/LightGBM/CatBoost ожидают метки 0, 1, ..., n_classes-1
        logger.info("\n   ✅ Маппинг меток для multiclass...")
        label_map = {-1: 0, 0: 1, 1: 2}
        reverse_label_map = {0: -1, 1: 0, 2: 1}

        y_train = y_train_raw.map(label_map)
        y_val = y_val_raw.map(label_map)
        y_test = y_test_raw.map(label_map)

        logger.info(f"   Маппинг: -1→0 (SL), 0→1 (Neutral), 1→2 (TP)")
        logger.info(f"   y_train уникальные: {sorted(y_train.unique())}")
        logger.info(f"   y_val уникальные: {sorted(y_val.unique())}")
        logger.info(f"   y_test уникальные: {sorted(y_test.unique())}")

        logger.info(f"\nX_train shape: {X_train.shape}")
        logger.info(f"y_train баланс (mapped): {y_train.value_counts().to_dict()}")
        
        # scale_pos_weight — ТОЛЬКО ДЛЯ BINARY!
        # ✅ Для multiclass (3 класса) scale_pos_weight не работает корректно
        # ✅ XGBoost/LightGBM multiclass используют class_weight автоматически
        logger.info(f"\n   Баланс классов (mapped):")
        for cls in [0, 1, 2]:
            count = (y_train == cls).sum()
            pct = count / len(y_train) * 100
            orig_cls = reverse_label_map[cls]
            logger.info(f"      Класс {cls} (orig {orig_cls}): {count:,} ({pct:.1f}%)")
        logger.info("   ❌ SMOTE НЕ используется (leakage для time series)")
        logger.info("   ⚠️ scale_pos_weight не используется для multiclass")

        # Оптимизация гиперпараметров для MULTICLASS
        if optimize_hyperparams:
            logger.info("   Запуск Optuna (multiclass)...")

            optimizer = HyperparameterOptimizer(
                n_trials=self.config.OPTUNA_TRIALS,
                timeout=self.config.OPTUNA_TIMEOUT
            )
            # ✅ Optuna для multiclass
            best_params = optimizer.optimize_multiclass(X_train, y_train, X_val, y_val, 'xgboost')

        # ✅ ВАЛИДАЦИЯ НА VAL после Optuna
        logger.info("\n   ✅ Валидация лучших параметров на val...")
        import xgboost as xgb
        
        # ✅ Multiclass XGBoost
        val_model = xgb.XGBClassifier(
            **best_params,
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss'
        )
        val_model.fit(X_train, y_train, verbose=False)
        val_pred_proba = val_model.predict_proba(X_val)
        
        # ✅ Multiclass ROC-AUC (one-vs-rest)
        val_roc_auc = roc_auc_score(y_val, val_pred_proba, multi_class='ovr', average='macro')
        logger.info(f"   Val ROC-AUC (multiclass): {val_roc_auc:.4f}")

        # Проверяем не переобучилась ли Optuna
        logger.info(f"   (Сравните с лучшим CV ROC-AUC из Optuna)")
        if not optimize_hyperparams:
            optimizer = HyperparameterOptimizer()
            best_params = optimizer._get_default_params_multiclass('xgboost')
        # ====================== СОЗДАНИЕ И ОБУЧЕНИЕ АНСАМБЛЯ ======================
        # ====================== СОЗДАНИЕ И ОБУЧЕНИЕ АНСАМБЛЯ ======================
        logger.info("\nCreating ensemble...")

        import xgboost as xgb
        from lightgbm import LGBMClassifier
        from catboost import CatBoostClassifier

        xgb_model = xgb.XGBClassifier(
            **best_params,
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss',
            early_stopping_rounds=self.config.EARLY_STOPPING_ROUNDS,
            random_state=42
        )

        lgb_model = LGBMClassifier(
            **{**best_params, 'verbose': -1, 'force_col_wise': True},
            objective='multiclass',
            num_class=3,
            random_state=42
        )

        cb_model = CatBoostClassifier(
            iterations=500,
            depth=6,
            learning_rate=0.05,
            loss_function='MultiClass',
            verbose=0,
            random_seed=42
        )

        self._estimators = [('xgb', xgb_model), ('lgb', lgb_model), ('cat', cb_model)]
        self._weights = np.array([0.45, 0.35, 0.20])

        # Обучаем модели
        for name, model in self._estimators:
            if name == 'xgb':
                model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
                logger.info(f"   ✅ {name} обучена с early stopping")
            else:
                model.fit(X_train, y_train)
                logger.info(f"   ✅ {name} обучена")

        # ====================== WEIGHTED ENSEMBLE + КАЛИБРОВКА ======================
        logger.info("\n   ✅ Создание weighted ensemble + калибровка...")

        from sklearn.isotonic import IsotonicRegression

        val_proba_raw = self._ensemble_predict_proba(X_val)
        calibrators = []
        for class_idx in range(3):
            iso = IsotonicRegression(out_of_bounds='clip')
            y_binary = (y_val == class_idx).astype(int)
            iso.fit(val_proba_raw[:, class_idx], y_binary)
            calibrators.append(iso)

        logger.info("   ✅ Isotonic калибровка завершена")

        # Mapper
        mapper = MulticlassSignalMapper().fit(self._estimators[0][1])

        # ====================== TEST EVALUATION ======================
        logger.info("\nОценка на TEST наборе...")

        X_test_clean = X_test.copy()
        for col in list(X_test_clean.columns):
            if X_test_clean[col].isnull().any():
                X_test_clean[f'{col}_is_missing'] = X_test_clean[col].isnull().astype(int)
                X_test_clean[col] = X_test_clean[col].fillna(X_train[col].median())
        X_test_clean = X_test_clean.fillna(-999)

        test_proba_raw = self._ensemble_predict_proba(X_test_clean)

        y_pred_proba = np.zeros_like(test_proba_raw)
        for i, iso in enumerate(calibrators):
            y_pred_proba[:, i] = iso.predict(test_proba_raw[:, i])

        y_pred_proba /= (y_pred_proba.sum(axis=1, keepdims=True) + 1e-8)

        y_pred_mapped = np.argmax(y_pred_proba, axis=1)
        y_pred = np.array([reverse_label_map[int(p)] for p in y_pred_mapped])

        y_test_mapped = y_test_raw.map(label_map).values

        logger.info(f"   ✅ Предсказания получены. Сигналы: {np.unique(y_pred)}")

        # Метрики
        metrics = {
            'accuracy': accuracy_score(y_test_mapped, y_pred_mapped),
            'roc_auc': roc_auc_score(y_test_mapped, y_pred_proba, multi_class='ovr', average='macro'),
            'precision': precision_score(y_test_mapped, y_pred_mapped, average='macro', zero_division=0),
            'recall': recall_score(y_test_mapped, y_pred_mapped, average='macro', zero_division=0),
            'f1': f1_score(y_test_mapped, y_pred_mapped, average='macro', zero_division=0),
            'sharpe': 0.0, 'sortino': 0.0, 'max_drawdown': 0.0,
            'total_return': 0.0, 'win_rate': 0.0, 'total_trades': 0
        }

        logger.info(f"\nМетрики на TEST:")
        logger.info(f"  Accuracy : {metrics['accuracy']:.4f}")
        logger.info(f"  ROC-AUC  : {metrics['roc_auc']:.4f}")
        logger.info(f"  F1-Score : {metrics['f1']:.4f}")

        # Backtesting
        logger.info("\n  📊 REAL BACKTESTING...")
        try:
            test_with_signals = test_df[['date', 'Name', 'close']].copy()
            test_with_signals['signal'] = y_pred

            simulator = PortfolioSimulator(
                initial_capital=100_000,
                max_positions=10,
                tb_window=Config.TB_WINDOW,
                commission=Config.COMMISSION,
                slippage=Config.SLIPPAGE,
                allow_shorts=False
            )
            results = simulator.run(test_with_signals)

            metrics.update({
                'sharpe': results.get('sharpe', 0),
                'sortino': results.get('sortino', 0),
                'max_drawdown': results.get('max_drawdown', 0),
                'total_return': results.get('total_return', 0),
                'win_rate': results.get('win_rate', 0),
                'total_trades': results.get('trades', 0)
            })
            logger.info(f"  Sharpe: {metrics['sharpe']:.3f} | Return: {metrics['total_return']:+.2f}%")
        except Exception as e:
            logger.warning(f"  Backtesting ошибка: {e}")

        # Сохранение модели (исправленное!)
        self.models['target'] = {
            'calibrators': calibrators,
            'weights': self._weights,
            'mapper': mapper
            # ensemble_predict_proba больше не сохраняем
        }
        self.feature_pipelines['target'] = feature_pipeline
        self.metrics['target'] = metrics

        # Feature Importance
        logger.info("\n6. FEATURE IMPORTANCE")
        self._calculate_feature_importance()

        logger.info("\n" + "=" * 80)
        logger.info("OK: TRAINING COMPLETED")
        logger.info("=" * 80)

        return self.metrics
    def _calculate_feature_importance(self):
        """Расчёт важности признаков"""
        model = self.models.get('target')
        
        # ✅ Если модель — CalibratedClassifierCV, достаём базовую модель
        if hasattr(model, 'estimator'):
            base_model = model.estimator
        else:
            base_model = model
        
        if base_model and hasattr(base_model, 'models'):
            importance = np.zeros(len(self.feature_pipelines['target'].feature_columns))

            for name, est in base_model.models:
                if hasattr(est, 'feature_importances_'):
                    importance += est.feature_importances_

            importance /= len(base_model.models)

            self.feature_importance['target'] = sorted(
                zip(self.feature_pipelines['target'].feature_columns, importance),
                key=lambda x: x[1],
                reverse=True
            )[:20]

            logger.info(f"\nТоп-5 признаков:")
            for i, (feat, imp) in enumerate(self.feature_importance['target'][:5], 1):
                logger.info(f"  {i}. {feat}: {imp:.4f}")
    
    def save(self, path: str = None):
        """Сохранение модели"""
        if path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = str(self.config.MODEL_DIR / f'model_ultimate_v4_{timestamp}.joblib')
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'models': self.models,
            'feature_pipelines': self.feature_pipelines,
            'metrics': self.metrics,
            'feature_importance': self.feature_importance,
            'config': {
                'horizons': self.config.HORIZONS,
                'optuna_trials': self.config.OPTUNA_TRIALS,
                'cv_splits': self.config.CV_SPLITS,
                'gap_days': self.config.GAP_DAYS
            }
        }
        
        joblib.dump(model_data, path)
        logger.info(f"💾 Модель сохранена: {path}")
        
        # Сохранение метрик
        metrics_path = str(self.config.MODEL_DIR / f'metrics_ultimate_v4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        logger.info(f"💾 Метрики сохранены: {metrics_path}")
        
        return path
    
    @classmethod
    def load(cls, path: str, config: Config = None):
        """Загрузка модели"""
        instance = cls(config)
        model_data = joblib.load(path)
        
        instance.models = model_data['models']
        instance.feature_pipelines = model_data['feature_pipelines']
        instance.metrics = model_data['metrics']
        instance.feature_importance = model_data['feature_importance']
        
        return instance

def train_ultimate_v4():
    """Обучение финальной модели v4.0"""
    config = Config()
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("INVESTEDU ML MODEL v4.0 — MAXIMUM PERFORMANCE")
    logger.info("=" * 80)

    # Загрузка данных
    logger.info("\n1. ЗАГРУЗКА ДАННЫХ")

    from train_ultimate_v3 import AdvancedDataLoader
    loader = AdvancedDataLoader()

    # Загружаем ВСЕ 249 тикеров!
    prices = loader.load_moex_stocks(n_tickers=249)
    macro = loader.load_macro_ru()

    if len(prices) == 0:
        logger.error("Нет данных для обучения!")
        return

    logger.info(f"   Всего: {len(prices):,} строк, {prices['Name'].nunique()} тикеров")

    # Слияние
    df = loader.merge_data(prices, macro)
    
    # Обучение модели
    model = UltimateEnsembleModelV4(config)
    metrics = model.fit(df, optimize_hyperparams=True)
    
    # Сохранение
    model.save()

    # Итоги
    logger.info("\n" + "=" * 80)
    logger.info("OK: TRAINING COMPLETED!")
    logger.info("=" * 80)

    logger.info("\nFINAL METRICS:")
    m = metrics.get('target', {})
    
    # ✅ Безопасное форматирование (защита от str вместо float)
    roc_auc = m.get('roc_auc', 'N/A')
    accuracy = m.get('accuracy', 'N/A')
    sharpe = m.get('sharpe', 'N/A')
    total_return = m.get('total_return', 'N/A')
    
    if isinstance(roc_auc, (int, float)):
        logger.info(f"  ROC-AUC: {roc_auc:.4f}")
    else:
        logger.info(f"  ROC-AUC: {roc_auc}")
        
    if isinstance(accuracy, (int, float)):
        logger.info(f"  Accuracy: {accuracy:.4f}")
    else:
        logger.info(f"  Accuracy: {accuracy}")
        
    if isinstance(sharpe, (int, float)):
        logger.info(f"  Sharpe: {sharpe:.3f}")
    else:
        logger.info(f"  Sharpe: {sharpe}")
        
    if isinstance(total_return, (int, float)):
        logger.info(f"  Total Return: {total_return:.2f}%")
    else:
        logger.info(f"  Total Return: {total_return}")
    
    logger.info("\nModel is ready to use!")
    
    return model


if __name__ == "__main__":
    train_ultimate_v4()

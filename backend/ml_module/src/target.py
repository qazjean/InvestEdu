"""
Этап 3: Создание целевой переменной (target)
Этап 4: Подготовка данных для модели

Создание target переменной:
- future_close — цена закрытия через 30 дней
- target = 1 если future_close > close (акция выросла)
- target = 0 если future_close <= close (акция не выросла)

Подготовка данных:
- Выбор признаков
- Разделение на train/test (80/20 по времени)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from pathlib import Path
import joblib


class TargetCreator:
    """Создание целевой переменной"""
    
    def __init__(self, tickers_data: Dict[str, pd.DataFrame]):
        self.tickers_data = tickers_data
        self.processed_data = {}
    
    def create_target(self, df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
        """Создание target переменной"""
        df = df.copy()
        
        # Future close (цена через N дней)
        df['future_close'] = df['close'].shift(-days)
        
        # Target: 1 если цена вырастет, 0 если нет
        df['target'] = (df['future_close'] > df['close']).astype(int)
        
        return df
    
    def remove_future_nan(self, df: pd.DataFrame) -> pd.DataFrame:
        """Удаление строк где future_close недоступен"""
        df = df.copy()
        rows_before = len(df)
        df = df.dropna(subset=['future_close', 'target'])
        rows_after = len(df)
        
        print(f"   Удалено {rows_before - rows_after} строк (future_close недоступен)")
        
        return df
    
    def process_all(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """Обработка всех тикеров"""
        print("=" * 70)
        print("📊 ЭТАП 3: СОЗДАНИЕ ЦЕЛЕВОЙ ПЕРЕМЕННОЙ")
        print("=" * 70)
        print()
        
        print(f"🎯 Прогноз на {days} дней вперёд...")
        print()
        
        for ticker, data in self.tickers_data.items():
            data = self.create_target(data, days)
            data = self.remove_future_nan(data)
            self.processed_data[ticker] = data
        
        # Статистика target
        total = sum(len(df) for df in self.processed_data.values())
        positive = sum(df['target'].sum() for df in self.processed_data.values())
        
        print(f"✅ Всего примеров: {total:,}")
        print(f"   Рост (target=1): {positive:,} ({positive/total*100:.1f}%)")
        print(f"   Падение (target=0): {total-positive:,} ({(total-positive)/total*100:.1f}%)")
        print()
        
        print("=" * 70)
        print("✅ ЭТАП 3 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return self.processed_data


class DataPreparator:
    """Подготовка данных для модели"""
    
    def __init__(self, tickers_data: Dict[str, pd.DataFrame]):
        self.tickers_data = tickers_data
        self.feature_columns = [
            # Технические (оригинальные)
            'open', 'high', 'low', 'close', 'volume',
            'MA20', 'MA50', 'MA200',
            'close_MA20_ratio', 'close_MA50_ratio', 'close_MA200_ratio',
            'daily_return', 'volatility_30', 'momentum_10_ratio',
            'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
            'volume_MA20', 'volume_ratio',
            'HL_range_pct', 'CO_ratio', 'position_in_range',
            
            # Индексы
            'index_IMOEX', 'index_SPX', 'index_VIX',
            'index_IMOEX_return', 'index_SPX_return', 'index_VIX_return',
            
            # Макро
            'key_rate', 'usd_rub', 'eur_rub',
            'usd_rub_change', 'key_rate_change',
            'usd_rub_lag1', 'key_rate_lag1',
            
            # Фундаментальные (будут добавлены динамически)
            # 'fund_pe_ratio', 'fund_pb_ratio', 'fund_dividend_yield',
            # 'fund_market_cap', 'fund_roe', 'fund_debt_to_equity',
            # 'fund_revenue_growth', 'fund_profit_margin', 'fund_beta'
        ]
    
    def add_fundamental_features(self, fundamental_features: list):
        """Добавление фундаментальных признаков"""
        for feat in fundamental_features:
            col_name = f'fund_{feat}'
            if col_name not in self.feature_columns:
                self.feature_columns.append(col_name)
    
    def select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Выбор признаков"""
        available_cols = [col for col in self.feature_columns if col in df.columns]
        return df[available_cols]
    
    def prepare_train_test(
        self, 
        test_size: float = 0.2,
        by_time: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Подготовка train/test наборов
        
        Args:
            test_size: доля test набора
            by_time: если True, разделение по времени (не случайно)
        """
        print("=" * 70)
        print("📊 ЭТАП 4: ПОДГОТОВКА ДАННЫХ ДЛЯ МОДЕЛИ")
        print("=" * 70)
        print()
        
        # Объединение всех данных
        all_data = []
        for ticker, df in self.tickers_data.items():
            df = df.copy()
            df['ticker'] = ticker
            all_data.append(df)
        
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined.sort_values(['ticker', 'date']).reset_index(drop=True)
        
        print(f"📈 Всего примеров: {len(combined):,}")
        print()
        
        # Выбор признаков
        X = self.select_features(combined)
        y = combined['target']
        
        print(f"📋 Признаков: {len(X.columns)}")
        print(f"   {X.columns.tolist()}")
        print()
        
        # Разделение по времени
        if by_time:
            print("⏰ Разделение по времени (train — раньше, test — позже)...")
            
            # Для каждого тикера берём последние 20% как test
            train_list = []
            test_list = []
            
            for ticker in combined['ticker'].unique():
                ticker_data = combined[combined['ticker'] == ticker]
                split_idx = int(len(ticker_data) * (1 - test_size))
                
                train_list.append(ticker_data.iloc[:split_idx])
                test_list.append(ticker_data.iloc[split_idx:])
            
            train_data = pd.concat(train_list, ignore_index=True)
            test_data = pd.concat(test_list, ignore_index=True)
            
            X_train = self.select_features(train_data)
            X_test = self.select_features(test_data)
            y_train = train_data['target']
            y_test = test_data['target']
            
        else:
            # Случайное разделение
            from sklearn.model_selection import train_test_split
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        
        print(f"✅ Train: {len(X_train):,} примеров")
        print(f"✅ Test: {len(X_test):,} примеров")
        print()
        
        # Баланс классов
        print("📊 Баланс классов:")
        print(f"   Train: target=1 — {y_train.sum():,} ({y_train.mean()*100:.1f}%)")
        print(f"   Test: target=1 — {y_test.sum():,} ({y_test.mean()*100:.1f}%)")
        print()
        
        print("=" * 70)
        print("✅ ЭТАП 4 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return X_train, X_test, y_train, y_test
    
    def save_data(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        output_dir: Path
    ):
        """Сохранение данных"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохранить как CSV
        X_train.to_csv(output_dir / 'X_train.csv', index=False)
        X_test.to_csv(output_dir / 'X_test.csv', index=False)
        y_train.to_csv(output_dir / 'y_train.csv', index=False)
        y_test.to_csv(output_dir / 'y_test.csv', index=False)
        
        print(f"💾 Данные сохранены в {output_dir}")
        print()


if __name__ == "__main__":
    from data_loader import DataLoader
    from features import FeatureEngineer
    from pathlib import Path
    
    # Загрузка данных
    DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    loader = DataLoader(DATA_DIR)
    tickers_data = loader.process_all()
    
    # Feature Engineering
    fe = FeatureEngineer(tickers_data)
    processed_data = fe.process_all()
    fe.remove_nan_rows()
    
    # Создание target
    tc = TargetCreator(fe.processed_data)
    target_data = tc.process_all(days=30)
    
    # Подготовка данных
    dp = DataPreparator(tc.processed_data)
    X_train, X_test, y_train, y_test = dp.prepare_train_test(test_size=0.2)
    
    # Сохранение
    OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
    dp.save_data(X_train, X_test, y_train, y_test, OUTPUT_DIR)

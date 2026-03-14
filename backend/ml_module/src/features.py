"""
Этап 2: Feature Engineering (создание признаков)

Расчёт технических индикаторов для каждой акции:
- Скользящие средние (MA20, MA50, MA200)
- Momentum показатели (Daily return, Volatility)
- Технические индикаторы (RSI, MACD)
- Объём (Volume MA20)
- Дополнительные признаки
- Фундаментальные признаки (P/E, P/B, и т.д.)
- Рыночные признаки (индексы, VIX)
"""

import pandas as pd
import numpy as np
from typing import Dict


class FeatureEngineer:
    """Создание признаков для модели"""
    
    def __init__(self, tickers_data: Dict[str, pd.DataFrame]):
        self.tickers_data = tickers_data
        self.processed_data = {}
        self.fundamental_data = None
        self.indices_data = None
        self.macro_data = None
    
    def set_fundamental_data(self, df: pd.DataFrame):
        """Установка фундаментальных данных"""
        self.fundamental_data = df
    
    def set_indices_data(self, df: pd.DataFrame):
        """Установка данных индексов"""
        self.indices_data = df
    
    def set_macro_data(self, df: pd.DataFrame):
        """Установка макро данных"""
        self.macro_data = df
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт скользящих средних"""
        df = df.copy()
        
        # MA20, MA50, MA200
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        df['MA200'] = df['close'].rolling(window=200).mean()
        
        # Цена относительно MA
        df['close_MA20_ratio'] = df['close'] / df['MA20']
        df['close_MA50_ratio'] = df['close'] / df['MA50']
        df['close_MA200_ratio'] = df['close'] / df['MA200']
        
        return df
    
    def calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт momentum показателей"""
        df = df.copy()
        
        # Daily return
        df['daily_return'] = df['close'].pct_change()
        
        # Volatility (30 дней)
        df['volatility_30'] = df['daily_return'].rolling(window=30).std()
        
        # Momentum (10 дней)
        df['momentum_10'] = df['close'] - df['close'].shift(10)
        df['momentum_10_ratio'] = df['momentum_10'] / df['close'].shift(10)
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Расчёт RSI (Relative Strength Index)"""
        df = df.copy()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт MACD"""
        df = df.copy()
        
        # MACD line (12, 26)
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        
        # Signal line (9)
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # MACD histogram
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        return df
    
    def calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт признаков объёма"""
        df = df.copy()
        
        # Volume MA20
        df['volume_MA20'] = df['volume'].rolling(window=20).mean()
        
        # Volume ratio
        df['volume_ratio'] = df['volume'] / df['volume_MA20']
        
        return df
    
    def calculate_additional_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт дополнительных признаков"""
        df = df.copy()
        
        # High-Low range
        df['HL_range'] = df['high'] - df['low']
        df['HL_range_pct'] = df['HL_range'] / df['close']
        
        # Close-Open ratio
        df['CO_ratio'] = df['close'] / df['open']
        
        # Price position in range
        df['position_in_range'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        return df
    
    def process_ticker(self, ticker: str, df: pd.DataFrame) -> pd.DataFrame:
        """Обработка одного тикера"""
        df = df.copy()
        
        # Все технические признаки
        df = self.calculate_moving_averages(df)
        df = self.calculate_momentum(df)
        df = self.calculate_rsi(df)
        df = self.calculate_macd(df)
        df = self.calculate_volume_features(df)
        df = self.calculate_additional_features(df)
        
        # Добавление фундаментальных данных
        if self.fundamental_data is not None:
            df = self._merge_fundamentals(df, ticker)
        
        # Добавление данных индексов
        if self.indices_data is not None:
            df = self._merge_indices(df)
        
        # Добавление макро данных
        if self.macro_data is not None:
            df = self._merge_macro(df)
        
        return df
    
    def _merge_fundamentals(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Слияние с фундаментальными данными"""
        ticker_clean = ticker.replace('.ME', '')
        
        fund = self.fundamental_data[self.fundamental_data['ticker'] == ticker_clean]
        
        if len(fund) > 0:
            # Берём последние доступные фундаментальные данные
            fund_row = fund.iloc[-1]
            
            # Добавляем как константы для всех дат
            for col in fund_row.index:
                if col not in ['ticker', 'date', 'company_name']:
                    df[f'fund_{col}'] = fund_row[col]
        
        return df
    
    def _merge_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Слияние с данными индексов"""
        if self.indices_data is None:
            return df
        
        # Преобразование даты
        df['date'] = pd.to_datetime(df['date'])
        
        # Для каждого индекса
        for index_name in ['IMOEX', 'SPX', 'VIX']:
            index_data = self.indices_data[self.indices_data['index_name'] == index_name]
            
            if len(index_data) > 0:
                index_data = index_data[['date', 'close']].copy()
                index_data = index_data.rename(columns={'close': f'index_{index_name}'})
                
                # Merge
                df = df.merge(index_data, on='date', how='left')
                df[f'index_{index_name}'] = df[f'index_{index_name}'].ffill()
                
                # Доходность индекса
                df[f'index_{index_name}_return'] = df[f'index_{index_name}'].pct_change()
        
        return df
    
    def _merge_macro(self, df: pd.DataFrame) -> pd.DataFrame:
        """Слияние с макро данными"""
        if self.macro_data is None:
            return df
        
        # Преобразование даты
        df['date'] = pd.to_datetime(df['date'])
        
        # Merge с макро данными
        macro_cols = ['date', 'key_rate', 'usd_rub', 'eur_rub', 'usd_rub_change', 
                      'key_rate_change', 'usd_rub_lag1', 'key_rate_lag1']
        available_cols = [c for c in macro_cols if c in self.macro_data.columns]
        
        df = df.merge(self.macro_data[available_cols], on='date', how='left')
        
        # Forward fill для макро данных
        for col in ['key_rate', 'usd_rub', 'eur_rub']:
            if col in df.columns:
                df[col] = df[col].ffill()
        
        return df
    
    def process_all(self) -> Dict[str, pd.DataFrame]:
        """Обработка всех тикеров"""
        print("=" * 70)
        print("📊 ЭТАП 2: FEATURE ENGINEERING")
        print("=" * 70)
        print()
        
        print("🔄 Расчёт технических индикаторов...")
        
        for ticker, data in self.tickers_data.items():
            self.processed_data[ticker] = self.process_ticker(ticker, data)
        
        print(f"✅ Обработано {len(self.processed_data)} тикеров")
        print()
        
        # Показать созданные признаки
        sample_ticker = list(self.processed_data.keys())[0]
        sample_df = self.processed_data[sample_ticker]
        
        print("📋 Созданные признаки:")
        feature_cols = [col for col in sample_df.columns if col not in ['date', 'Name', 'open', 'high', 'low', 'close', 'volume']]
        for col in feature_cols:
            print(f"   • {col}")
        print()
        
        print("=" * 70)
        print("✅ ЭТАП 2 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return self.processed_data
    
    def remove_nan_rows(self, min_rows: int = 200) -> Dict[str, pd.DataFrame]:
        """Удаление строк с NaN (после расчёта индикаторов)"""
        print("🧹 Удаление строк с NaN...")
        
        for ticker, data in self.processed_data.items():
            rows_before = len(data)
            data = data.dropna()
            rows_after = len(data)
            
            if rows_after >= min_rows:
                self.processed_data[ticker] = data
                print(f"   {ticker}: {rows_before} → {rows_after} строк")
            else:
                print(f"   ❌ {ticker}: недостаточно данных ({rows_after} < {min_rows})")
        
        print(f"✅ Осталось {len(self.processed_data)} тикеров")
        print()
        
        return self.processed_data


if __name__ == "__main__":
    from data_loader import DataLoader
    from pathlib import Path
    
    # Загрузка данных
    DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    loader = DataLoader(DATA_DIR)
    tickers_data = loader.process_all()
    
    # Feature Engineering
    fe = FeatureEngineer(tickers_data)
    processed_data = fe.process_all()
    
    # Удаление NaN
    fe.remove_nan_rows()
    
    # Сохранение
    OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Сохранить обработанные данные
    all_processed = pd.concat(processed_data.values(), ignore_index=True)
    all_processed.to_csv(OUTPUT_DIR / "stocks_with_features.csv", index=False)
    print(f"\n💾 Данные с признаками сохранены в {OUTPUT_DIR / 'stocks_with_features.csv'}")

"""
Этап 1: Загрузка и очистка данных

Загружает датасет исторических цен акций S&P 500 и выполняет:
1. Преобразование date в datetime
2. Сортировка по тикеру и дате
3. Удаление пропущенных значений
4. Разделение данных по тикерам
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os


class DataLoader:
    """Загрузка и очистка данных"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.df = None
        self.tickers_data = {}
    
    def load_csv(self, file_name: str = 'all_stocks_5yr.csv') -> pd.DataFrame:
        """Загрузка CSV файла"""
        file_path = self.data_path / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        print(f"📂 Загрузка данных из {file_path}...")
        self.df = pd.read_csv(file_path)
        print(f"✅ Загружено {len(self.df):,} строк")
        
        return self.df
    
    def convert_dates(self, date_column: str = 'date') -> pd.DataFrame:
        """Преобразование колонки даты в datetime"""
        print("📅 Преобразование дат...")
        self.df[date_column] = pd.to_datetime(self.df[date_column])
        print(f"✅ Диапазон дат: {self.df[date_column].min()} — {self.df[date_column].max()}")
        
        return self.df
    
    def sort_data(self, ticker_column: str = 'Name', date_column: str = 'date') -> pd.DataFrame:
        """Сортировка по тикеру и дате"""
        print("📊 Сортировка данных...")
        self.df = self.df.sort_values([ticker_column, date_column]).reset_index(drop=True)
        print(f"✅ Отсортировано по {ticker_column} и {date_column}")
        
        return self.df
    
    def handle_missing_values(self) -> pd.DataFrame:
        """Проверка и удаление пропущенных значений"""
        print("🔍 Проверка пропущенных значений...")
        
        missing_before = self.df.isnull().sum().sum()
        print(f"   Пропущено значений: {missing_before:,}")
        
        if missing_before > 0:
            self.df = self.df.dropna()
            missing_after = self.df.isnull().sum().sum()
            print(f"   Удалено строк: {missing_before - missing_after:,}")
        
        print(f"✅ Осталось {len(self.df):,} строк")
        
        return self.df
    
    def split_by_ticker(self, ticker_column: str = 'Name') -> dict:
        """Разделение данных по тикерам"""
        print("📈 Разделение по тикерам...")
        
        self.tickers_data = {
            ticker: group.copy() 
            for ticker, group in self.df.groupby(ticker_column)
        }
        
        print(f"✅ Найдено {len(self.tickers_data)} тикеров")
        print(f"   Примеры: {list(self.tickers_data.keys())[:10]}")
        
        return self.tickers_data
    
    def get_data_summary(self) -> pd.DataFrame:
        """Получить сводку по данным"""
        summary = []
        
        for ticker, data in self.tickers_data.items():
            summary.append({
                'ticker': ticker,
                'rows': len(data),
                'date_start': data['date'].min(),
                'date_end': data['date'].max(),
                'avg_volume': data['volume'].mean(),
                'avg_close': data['close'].mean()
            })
        
        return pd.DataFrame(summary)
    
    def process_all(self) -> dict:
        """Выполнить все этапы загрузки и очистки"""
        print("=" * 70)
        print("🚀 ЭТАП 1: ЗАГРУЗКА И ОЧИСТКА ДАННЫХ")
        print("=" * 70)
        print()
        
        self.load_csv()
        print()
        
        self.convert_dates()
        print()
        
        self.sort_data()
        print()
        
        self.handle_missing_values()
        print()
        
        self.split_by_ticker()
        print()
        
        print("=" * 70)
        print("✅ ЭТАП 1 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return self.tickers_data


if __name__ == "__main__":
    # Пути к данным
    DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    
    # Загрузка данных
    loader = DataLoader(DATA_DIR)
    tickers_data = loader.process_all()
    
    # Показать сводку
    summary = loader.get_data_summary()
    print("\n📊 Сводка по тикерам (первые 10):")
    print(summary.head(10).to_string(index=False))
    
    # Сохранить обработанные данные
    OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Сохранить полный датасет
    loader.df.to_csv(OUTPUT_DIR / "stocks_cleaned.csv", index=False)
    print(f"\n💾 Данные сохранены в {OUTPUT_DIR / 'stocks_cleaned.csv'}")
    
    # Сохранить сводку
    summary.to_csv(OUTPUT_DIR / "stocks_summary.csv", index=False)
    print(f"💾 Сводка сохранена в {OUTPUT_DIR / 'stocks_summary.csv'}")

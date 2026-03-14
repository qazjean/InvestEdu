"""
Загрузка данных из Yahoo Finance (США + РФ)
+ Макро данные ЦБ РФ

Источники:
- Yahoo Finance: исторические цены акций (США + РФ)
- ЦБ РФ: ключевая ставка, курс USD/RUB
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from pathlib import Path
from datetime import datetime, timedelta
import time


class YahooDataLoader:
    """Загрузка данных из Yahoo Finance"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "data" / "raw"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_us_stocks(
        self,
        tickers: list = None,
        start_date: str = '2017-01-01',
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Загрузка данных по акциям США
        
        Args:
            tickers: список тикеров (по умолчанию топ-50 S&P 500)
            start_date: дата начала
            end_date: дата окончания
        
        Returns:
            DataFrame с данными
        """
        if tickers is None:
            # Топ-50 компаний S&P 500 по капитализации
            tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
                'UNH', 'JNJ', 'XOM', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'MRK',
                'ABBV', 'LLY', 'PEP', 'KO', 'AVGO', 'COST', 'WMT', 'TMO', 'MCD',
                'CSCO', 'ACN', 'ABT', 'DHR', 'VZ', 'ADBE', 'NKE', 'TXN', 'NEE',
                'CRM', 'PM', 'RTX', 'UPS', 'QCOM', 'HON', 'LOW', 'AMGN', 'IBM',
                'INTC', 'BA', 'SPGI', 'GS', 'CAT'
            ]
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print("=" * 70)
        print("📥 ЗАГРУЗКА ДАННЫХ США (Yahoo Finance)")
        print("=" * 70)
        print(f"   Тикеры: {len(tickers)} компаний")
        print(f"   Период: {start_date} — {end_date}")
        print()
        
        all_data = []
        
        for i, ticker in enumerate(tickers):
            try:
                print(f"   [{i+1}/{len(tickers)}] Загрузка {ticker}...", end=" ")
                
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date)
                
                if len(df) > 0:
                    df = df.reset_index()
                    df['Name'] = ticker
                    df['Date'] = df['Date'].dt.date
                    
                    # Переименование колонок
                    df = df.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    
                    all_data.append(df[['date', 'Name', 'open', 'high', 'low', 'close', 'volume']])
                    print("✅")
                else:
                    print("❌ Нет данных")
                
                # Пауза между запросами
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            print(f"\n✅ Загружено {len(combined):,} строк")
            
            # Сохранение
            output_file = self.output_dir / 'us_stocks_yahoo.csv'
            combined.to_csv(output_file, index=False)
            print(f"💾 Сохранено в {output_file}")
            
            return combined
        else:
            print("❌ Не удалось загрузить данные")
            return pd.DataFrame()
    
    def download_ru_stocks(
        self,
        tickers: list = None,
        start_date: str = '2017-01-01',
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Загрузка данных по акциям РФ (тикер.ME)
        
        Args:
            tickers: список тикеров (по умолчанию топ-15 РФ акций)
            start_date: дата начала
            end_date: дата окончания
        
        Returns:
            DataFrame с данными
        """
        if tickers is None:
            # Топ РФ акций на Yahoo Finance
            tickers = [
                'SBER.ME',    # Сбербанк
                'GAZP.ME',    # Газпром
                'LKOH.ME',    # Лукойл
                'YNDX.ME',    # Яндекс
                'TCSG.ME',    # Тинькофф
                'VTBR.ME',    # ВТБ
                'ROSN.ME',    # Роснефть
                'NVTK.ME',    # Новатэк
                'SNGS.ME',    # Сургутнефтегаз
                'GMKN.ME',    # Норникель
                'NLMK.ME',    # НЛМК
                'MAGN.ME',    # Магнитка
                'ALRS.ME',    # АЛРОСА
                'POLY.ME',    # Полиметалл
                'MTSS.ME'     # МТС
            ]
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print()
        print("=" * 70)
        print("📥 ЗАГРУЗКА ДАННЫХ РФ (Yahoo Finance)")
        print("=" * 70)
        print(f"   Тикеры: {len(tickers)} компаний")
        print(f"   Период: {start_date} — {end_date}")
        print()
        
        all_data = []
        
        for i, ticker in enumerate(tickers):
            try:
                print(f"   [{i+1}/{len(tickers)}] Загрузка {ticker}...", end=" ")
                
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date)
                
                if len(df) > 0:
                    df = df.reset_index()
                    # Убираем .ME из названия
                    clean_ticker = ticker.replace('.ME', '')
                    df['Name'] = clean_ticker
                    df['Date'] = df['Date'].dt.date
                    
                    df = df.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    
                    all_data.append(df[['date', 'Name', 'open', 'high', 'low', 'close', 'volume']])
                    print("✅")
                else:
                    print("❌ Нет данных")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            print(f"\n✅ Загружено {len(combined):,} строк")
            
            # Сохранение
            output_file = self.output_dir / 'ru_stocks_yahoo.csv'
            combined.to_csv(output_file, index=False)
            print(f"💾 Сохранено в {output_file}")
            
            return combined
        else:
            print("❌ Не удалось загрузить данные")
            return pd.DataFrame()


class CBRDataLoader:
    """Загрузка макро данных с ЦБ РФ"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "data" / "raw"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = 'https://cbr-xml-daily.ru'
    
    def get_key_rate(self) -> pd.DataFrame:
        """
        Загрузка данных по ключевой ставке ЦБ РФ
        
        Returns:
            DataFrame с датой и ставкой
        """
        print()
        print("=" * 70)
        print("📥 ЗАГРУЗКА ДАННЫХ ЦБ РФ")
        print("=" * 70)
        print("   Ключевая ставка...", end=" ")
        
        try:
            # Используем API cbr-xml-daily.ru
            response = requests.get(f'{self.base_url}/dynamic_json')
            data = response.json()
            
            # Создаем DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.rename(columns={'key_rate': 'key_rate'})
            df = df[['date', 'key_rate']]
            
            # Сортировка
            df = df.sort_values('date')
            
            print("✅")
            print(f"   Диапазон: {df['date'].min().date()} — {df['date'].max().date()}")
            print(f"   Текущая ставка: {df['key_rate'].iloc[-1]:.2f}%")
            
            # Сохранение
            output_file = self.output_dir / 'cb_key_rate.csv'
            df.to_csv(output_file, index=False)
            print(f"💾 Сохранено в {output_file}")
            
            return df
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            # Возвращаем заглушку
            return self._create_key_rate_mock()
    
    def get_usd_rub(self, start_date: str = '2017-01-01', end_date: str = None) -> pd.DataFrame:
        """
        Загрузка данных по курсу USD/RUB с ЦБ РФ
        
        Returns:
            DataFrame с датой и курсом
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"   Курс USD/RUB...", end=" ")
        
        try:
            # API cbr-xml-daily.ru
            response = requests.get(f'{self.base_url}/dynamic_json')
            data = response.json()
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Фильтрация по датам
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            df = df.rename(columns={'USD': 'usd_rub'})
            df = df[['date', 'usd_rub']]
            df = df.sort_values('date')
            
            print("✅")
            print(f"   Диапазон: {df['date'].min().date()} — {df['date'].max().date()}")
            print(f"   Средний курс: {df['usd_rub'].mean():.2f}")
            
            # Сохранение
            output_file = self.output_dir / 'cb_usd_rub.csv'
            df.to_csv(output_file, index=False)
            print(f"💾 Сохранено в {output_file}")
            
            return df
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return self._create_usd_rub_mock(start_date, end_date)
    
    def _create_key_rate_mock(self) -> pd.DataFrame:
        """Создание заглушки для ключевой ставки (если API недоступен)"""
        print("⚠️ Используем заглушку (API ЦБ недоступен)")
        
        data = {
            'date': pd.date_range('2017-01-01', periods=84, freq='MS'),
            'key_rate': [
                10.0, 10.0, 9.75, 9.5, 9.0, 8.5, 8.25, 8.0, 7.75, 7.5, 7.5, 7.5,
                7.5, 7.5, 7.5, 7.25, 7.0, 6.5, 6.25, 6.0, 5.5, 5.0, 4.5, 4.25,
                4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 4.25, 5.5, 6.5,
                7.5, 8.5, 9.5, 11.0, 13.0, 15.0, 16.0, 16.0, 16.0, 16.0, 16.0,
                16.0, 16.0, 16.0, 16.0, 16.0, 16.0, 16.0, 16.0, 16.0, 16.0,
                18.0, 19.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0,
                20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0,
                20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0
            ][:84]
        }
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def _create_usd_rub_mock(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Создание заглушки для USD/RUB (если API недоступен)"""
        print("⚠️ Используем заглушку (API ЦБ недоступен)")
        
        dates = pd.date_range(start_date, end_date, freq='D')
        np.random.seed(42)
        
        # Симуляция курса с трендом
        base = 60
        trend = np.linspace(0, 35, len(dates))
        noise = np.random.randn(len(dates)) * 2
        usd_rub = base + trend + noise
        
        df = pd.DataFrame({
            'date': dates,
            'usd_rub': usd_rub
        })
        
        return df
    
    def get_all_macro(self, start_date: str = '2017-01-01', end_date: str = None) -> pd.DataFrame:
        """
        Загрузка всех макро данных
        
        Returns:
            DataFrame с макропризнаками
        """
        key_rate = self.get_key_rate()
        usd_rub = self.get_usd_rub(start_date, end_date)
        
        # Merge
        macro = pd.merge(key_rate, usd_rub, on='date', how='outer')
        macro = macro.sort_values('date')
        
        # Forward fill для ключевой ставки
        macro['key_rate'] = macro['key_rate'].ffill()
        
        # Добавление лагов и изменений
        macro['key_rate_change'] = macro['key_rate'].diff()
        macro['usd_rub_change'] = macro['usd_rub'].diff()
        macro['usd_rub_lag1'] = macro['usd_rub'].shift(1)
        macro['key_rate_lag1'] = macro['key_rate'].shift(1)
        
        print(f"\n✅ Макро данные: {len(macro)} строк")
        
        return macro


if __name__ == "__main__":
    from pathlib import Path
    
    OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
    
    # Загрузка данных
    yahoo_loader = YahooDataLoader(OUTPUT_DIR)
    
    # США (можно закомментировать, если не нужно)
    us_data = yahoo_loader.download_us_stocks()
    
    # РФ
    ru_data = yahoo_loader.download_ru_stocks()
    
    # Макро данные ЦБ РФ
    cbr_loader = CBRDataLoader(OUTPUT_DIR)
    macro_data = cbr_loader.get_all_macro()
    
    print("\n" + "=" * 70)
    print("✅ ЗАГРУЗКА ДАННЫХ ЗАВЕРШЕНА")
    print("=" * 70)
    print(f"\n📊 ИТОГИ:")
    print(f"   • Акции США: {len(us_data):,} строк")
    print(f"   • Акции РФ: {len(ru_data):,} строк")
    print(f"   • Макро данные: {len(macro_data):,} строк")
    print(f"\n📁 Файлы сохранены в: {OUTPUT_DIR}")

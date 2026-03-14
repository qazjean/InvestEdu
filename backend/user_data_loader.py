"""
Загрузка данных пользователя (CSV с Мосбиржи)

Формат CSV Мосбиржи:
date,code,name,trades,volume,value,open,low,high,close
2024-01-10,SBER,Сбербанк,10000,1000000,285000000,285.5,284.0,287.0,286.5
...

Или пользователь может загрузить свой формат с колонками:
date, open, high, low, close, volume
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class UserDataLoader:
    """Загрузчик пользовательских данных"""
    
    def __init__(self):
        self.data = None
        self.ticker = None
    
    def load_csv(self, file_path: str, ticker: str = 'USER') -> pd.DataFrame:
        """
        Загрузка CSV файла

        Поддерживает форматы:
        - Investing.com: Date, Price, Open, High, Low, Vol.
        - Мосбиржа: date, open, high, low, close, volume
        - TradingEconomics: Date, Open, High, Low, Close, Volume

        Args:
            file_path: путь к CSV файлу
            ticker: тикер акции

        Returns:
            DataFrame с данными
        """
        print(f"📥 Загрузка CSV: {file_path}")

        # Пробуем разные кодировки
        encodings = ['utf-8', 'cp1251', 'latin1', 'iso-8859-1']
        df = None

        for encoding in encodings:
            try:
                # Читаем с разными параметрами для обработки кавычек
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    skipinitialspace=True,  # Пропускать пробелы после разделителя
                    thousands=',',  # Обрабатывать запятые как разделители тысяч
                    quotechar='"',  # Кавычки для строк
                    on_bad_lines='skip'  # Пропускать плохие строки
                )
                print(f"   ✅ Кодировка: {encoding}")
                break
            except Exception:
                continue

        if df is None:
            raise ValueError("Не удалось прочитать CSV файл")

        print(f"   ✅ Загружено {len(df)} строк")
        print(f"   📋 Колонки: {list(df.columns)}")

        # Нормализация колонок (поддержка разных форматов)
        df = self._normalize_columns(df)

        # Добавление тикера
        df['Name'] = ticker

        self.data = df
        self.ticker = ticker

        print(f"   📅 Период: {df['date'].min()} — {df['date'].max()}")
        
        # Проверка минимального количества данных
        if len(df) < 30:
            raise ValueError(f"Недостаточно данных: {len(df)} < 30 дней (минимум 30)")
        
        # Для расчёта MA200 нужно 200 дней
        if len(df) < 200:
            print(f"   ⚠️ Загружено {len(df)} дней (меньше 200)")
            print(f"   💡 Рекомендуется загрузить 200+ дней для точного прогноза")
            print(f"   💡 Модель всё равно сработает, но точность может быть ниже")

        return df
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Нормализация имён колонок"""
        
        print(f"   📋 Исходные колонки: {list(df.columns)}")

        # Маппинг русских названий в английские
        column_mapping = {
            # Мосбиржа
            'Дата': 'date',
            'Код': 'code',
            'Наименование': 'name',
            'Сделок': 'trades',
            'Объем': 'volume',
            'Срдзв. цена': 'avg_price',
            'Первая': 'open',
            'Мин': 'low',
            'Макс': 'high',
            'Закрытия': 'close',
            # Английские
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            # Investing.com формат (с кавычками и без)
            'Date': 'date',
            '"Date"': 'date',
            'Price': 'close',
            '"Price"': 'close',
            'Open': 'open',
            '"Open"': 'open',
            'High': 'high',
            '"High"': 'high',
            'Low': 'low',
            '"Low"': 'low',
            'Vol.': 'volume',
            '"Vol."': 'volume',
            'Change %': 'change_pct',
            '"Change %"': 'change_pct',
            # TradingEconomics
            'Close': 'close',
            '"Close"': 'close',
            'Volume': 'volume',
            '"Volume"': 'volume',
        }

        # Переименование колонок (очищаем от кавычек и пробелов)
        new_columns = []
        for col in df.columns:
            # Пробуем найти в маппинге сначала с кавычками, потом без
            col_clean = col.strip().strip('"').strip("'").strip()
            new_col = column_mapping.get(col, column_mapping.get(col_clean, col_clean))
            new_columns.append(new_col)
        
        df.columns = new_columns
        
        print(f"   📋 Нормализованные колонки: {list(df.columns)}")

        # Преобразование даты
        if 'date' in df.columns:
            # Пробуем разные форматы дат
            date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d %b %Y']
            for fmt in date_formats:
                try:
                    df['date'] = pd.to_datetime(df['date'], format=fmt)
                    break
                except:
                    continue
            
            # Если не получилось, пробуем автоматическое определение
            if df['date'].dtype == 'object':
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            df = df.sort_values('date')

        # Преобразование числовых колонок
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                # Удаляем кавычки, пробелы, проценты
                df[col] = df[col].astype(str).str.replace('"', '').str.replace("'", '')
                df[col] = df[col].str.replace(' ', '').str.replace(',', '')
                df[col] = df[col].str.replace('%', '')
                
                # Обрабатываем суффиксы объёмов (K, M, B)
                if col == 'volume':
                    def parse_volume(val):
                        if pd.isna(val) or val == '':
                            return None
                        val = str(val).upper()
                        multiplier = 1
                        if 'K' in val:
                            multiplier = 1000
                            val = val.replace('K', '')
                        elif 'M' in val:
                            multiplier = 1000000
                            val = val.replace('M', '')
                        elif 'B' in val:
                            multiplier = 1000000000
                            val = val.replace('B', '')
                        try:
                            return float(val) * multiplier
                        except:
                            return None
                    
                    df[col] = df[col].apply(parse_volume)
                else:
                    # Преобразуем в число
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        # Проверка обязательных колонок
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            print(f"   ❌ Отсутствуют колонки: {missing}")
            print(f"   💡 Доступные: {list(df.columns)}")
            raise ValueError(f"Отсутствуют обязательные колонки: {missing}")

        return df
    
    def load_macro_data(self) -> pd.DataFrame:
        """
        Загрузка макро данных ЦБ РФ за период данных пользователя
        
        Returns:
            DataFrame с макро данными
        """
        if self.data is None:
            raise ValueError("Сначала загрузите данные акции!")
        
        print()
        print("📥 Загрузка макро данных ЦБ РФ...")
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / 'ml_module' / 'src'))
        
        from macro_loader import CBRDataLoader
        
        macro_loader = CBRDataLoader()
        
        start_date = self.data['date'].min().strftime('%Y-%m-%d')
        end_date = self.data['date'].max().strftime('%Y-%m-%d')
        
        macro_df = macro_loader.get_all_macro(
            start_date=start_date,
            end_date=end_date,
            add_lags=True
        )
        
        # Слияние с данными акции
        print("   📊 Слияние данных...")
        merged = self.data.merge(macro_df, on='date', how='left')
        
        # Заполнение пропусков
        merged['key_rate'] = merged['key_rate'].ffill()
        merged['usd_rub'] = merged['usd_rub'].ffill()
        merged['oil_price'] = merged['oil_price'].ffill()
        
        print(f"   ✅ Макро данные загружены ({len(macro_df)} записей)")
        
        return merged
    
    def validate_data(self, min_days: int = 60) -> bool:
        """
        Проверка качества данных
        
        Args:
            min_days: минимальное количество дней
        
        Returns:
            True если данные валидны
        """
        if self.data is None:
            return False
        
        # Проверка количества дней
        if len(self.data) < min_days:
            print(f"❌ Недостаточно данных: {len(self.data)} < {min_days} дней")
            return False
        
        # Проверка пропусков
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if self.data[col].isnull().any():
                print(f"❌ Пропуски в колонке {col}")
                return False
        
        # Проверка отрицательных значений
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if (self.data[col] < 0).any():
                print(f"❌ Отрицательные значения в {col}")
                return False
        
        print("✅ Данные валидны")
        return True


def create_template_csv(output_path: str = 'stock_data_template.csv'):
    """Создание шаблона CSV для пользователя"""
    
    template = pd.DataFrame({
        'date': ['2024-01-10', '2024-01-11', '2024-01-12'],
        'open': [285.5, 286.5, 287.0],
        'high': [287.0, 288.0, 289.0],
        'low': [284.0, 285.5, 286.0],
        'close': [286.5, 287.0, 288.5],
        'volume': [1000000, 1200000, 1100000]
    })
    
    template.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ Шаблон создан: {output_path}")
    
    return output_path


if __name__ == "__main__":
    # Тест загрузчика
    print("=" * 80)
    print("🧪 ТЕСТ ЗАГРУЗЧИКА ДАННЫХ ПОЛЬЗОВАТЕЛЯ")
    print("=" * 80)
    print()
    
    # Создание шаблона
    create_template_csv()
    print()
    
    # Загрузка шаблона
    loader = UserDataLoader()
    df = loader.load_csv('stock_data_template.csv', ticker='SBER')
    
    # Проверка
    if loader.validate_data(min_days=2):
        print()
        print("✅ Тест пройден!")
        
        # Загрузка макро данных
        merged = loader.load_macro_data()
        print(f"   ✅ Слиты данные: {len(merged)} строк")
        print(f"   ✅ Признаков: {len(merged.columns)}")

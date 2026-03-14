"""
Этап 9: Макроэкономические данные для РФ рынка
Этап 10: Прогнозирование для пользователя

Добавление макроэкономических признаков:
- Ключевая ставка ЦБ
- Курс USD/RUB
- Цена нефти Brent

Прогнозирование для отдельной акции
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import joblib


class MacroDataLoader:
    """Загрузка макроэкономических данных"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "macro"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_key_rate(self) -> pd.DataFrame:
        """
        Загрузка данных по ключевой ставке ЦБ РФ
        
        Returns:
            DataFrame с датой и ставкой
        """
        # Пример данных (в реальности загружать из CSV или API)
        data = {
            'date': pd.date_range('2017-01-01', '2024-01-01', freq='MS'),
            'key_rate': [10.0, 9.5, 7.5, 7.5, 7.5, 6.5, 4.25, 4.25, 4.25, 5.5, 7.5, 9.5, 15.0, 16.0, 16.0]
        }
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def load_usd_rub(self) -> pd.DataFrame:
        """
        Загрузка данных по курсу USD/RUB
        
        Returns:
            DataFrame с датой и курсом
        """
        # В реальности загружать с MOEX или ЦБ
        np.random.seed(42)
        dates = pd.date_range('2017-01-01', '2024-01-01', freq='D')
        
        # Симуляция курса (от 55 до 100)
        base_rate = 60
        trend = np.linspace(0, 35, len(dates))
        noise = np.random.randn(len(dates)) * 2
        usd_rub = base_rate + trend + noise
        
        df = pd.DataFrame({
            'date': dates,
            'usd_rub': usd_rub
        })
        
        return df
    
    def load_oil_price(self) -> pd.DataFrame:
        """
        Загрузка данных по цене нефти Brent
        
        Returns:
            DataFrame с датой и ценой
        """
        np.random.seed(42)
        dates = pd.date_range('2017-01-01', '2024-01-01', freq='D')
        
        # Симуляция цены нефти (от 30 до 90)
        base_price = 55
        trend = np.sin(np.linspace(0, 4*np.pi, len(dates))) * 15
        noise = np.random.randn(len(dates)) * 5
        oil_price = base_price + trend + noise
        
        df = pd.DataFrame({
            'date': dates,
            'oil_price': oil_price
        })
        
        return df
    
    def merge_macro_features(
        self, 
        stock_df: pd.DataFrame,
        add_lags: bool = True
    ) -> pd.DataFrame:
        """
        Добавление макропризнаков к данным акции
        
        Args:
            stock_df: данные акции
            add_lags: добавить лаги макропризнаков
        
        Returns:
            DataFrame с макропризнаками
        """
        df = stock_df.copy()
        
        # Загрузка макро данных
        key_rate = self.load_key_rate()
        usd_rub = self.load_usd_rub()
        oil_price = self.load_oil_price()
        
        # Merge по дате
        df = df.merge(key_rate, on='date', how='left')
        df = df.merge(usd_rub, on='date', how='left')
        df = df.merge(oil_price, on='date', how='left')
        
        # Forward fill для ключевой ставки (месячные данные)
        df['key_rate'] = df['key_rate'].ffill()
        
        # Добавление лагов
        if add_lags:
            df['key_rate_lag1'] = df['key_rate'].shift(1)
            df['usd_rub_lag1'] = df['usd_rub'].shift(1)
            df['oil_price_lag1'] = df['oil_price'].shift(1)
            
            # Изменения
            df['key_rate_change'] = df['key_rate'].diff()
            df['usd_rub_change'] = df['usd_rub'].diff()
            df['oil_price_change'] = df['oil_price'].diff()
        
        return df


class StockPredictor:
    """Прогнозирование для акций"""
    
    def __init__(
        self, 
        model_path: Path,
        feature_columns: List[str],
        include_macro: bool = False
    ):
        self.model = joblib.load(model_path)
        self.feature_columns = feature_columns
        self.include_macro = include_macro
        self.macro_loader = MacroDataLoader(model_path.parent.parent) if include_macro else None
    
    def prepare_features(
        self, 
        stock_data: pd.DataFrame,
        ticker: str = None
    ) -> pd.DataFrame:
        """
        Подготовка признаков для прогноза
        
        Args:
            stock_data: исторические данные акции
            ticker: тикер акции
        
        Returns:
            DataFrame с признаками
        """
        from features import FeatureEngineer
        from target import TargetCreator
        
        # Расчёт признаков
        fe = FeatureEngineer({ticker: stock_data} if ticker else {'stock': stock_data})
        processed = fe.process_all()
        fe.remove_nan_rows()
        
        df = list(processed.values())[0]
        
        # Добавление макропризнаков
        if self.include_macro and self.macro_loader:
            df = self.macro_loader.merge_macro_features(df)
        
        return df
    
    def predict(
        self,
        stock_data: pd.DataFrame,
        ticker: str = 'UNKNOWN',
        n_days: int = 30
    ) -> Dict:
        """
        Прогноз для акции
        
        Args:
            stock_data: исторические данные
            ticker: тикер
            n_days: горизонт прогноза
        
        Returns:
            Dict с прогнозом
        """
        # Подготовка признаков
        df = self.prepare_features(stock_data, ticker)
        
        # Берём последнюю дату
        features = df[self.feature_columns].iloc[-1:].fillna(0)
        
        # Предсказание
        proba = self.model.predict_proba(features)[0, 1]
        prediction = self.model.predict(features)[0]
        
        # Анализ факторов
        from interpret import AIAnalyzer
        analyzer = AIAnalyzer(self.model, self.feature_columns)
        factors = analyzer._analyze_factors(features)
        
        # Макро данные
        macro_data = None
        if self.include_macro:
            macro_data = {
                'key_rate': df['key_rate'].iloc[-1] if 'key_rate' in df else None,
                'usd_rub': df['usd_rub'].iloc[-1] if 'usd_rub' in df else None,
                'oil_price': df['oil_price'].iloc[-1] if 'oil_price' in df else None
            }
        
        # Генерация отчёта
        report = analyzer._generate_report(ticker, proba, prediction, factors, macro_data)
        report['n_days'] = n_days
        report['last_price'] = df['close'].iloc[-1]
        
        return report
    
    def predict_multiple(
        self,
        stocks_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Прогноз для нескольких акций
        
        Args:
            stocks_data: dict {ticker: data}
        
        Returns:
            DataFrame с прогнозами
        """
        results = []
        
        for ticker, data in stocks_data.items():
            report = self.predict(data, ticker)
            results.append({
                'ticker': ticker,
                'probability': report['probability'],
                'prediction': report['prediction'],
                'recommendation': report['recommendation'],
                'last_price': report['last_price']
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('probability', ascending=False)
        
        return df


if __name__ == "__main__":
    from pathlib import Path
    
    # Пути
    MODEL_DIR = Path(__file__).parent.parent / "models" / "trained"
    
    # Признаки
    feature_columns = [
        'open', 'high', 'low', 'close', 'volume',
        'MA20', 'MA50', 'MA200', 'close_MA20_ratio', 'close_MA50_ratio',
        'close_MA200_ratio', 'daily_return', 'volatility_30', 'momentum_10_ratio',
        'RSI', 'MACD', 'MACD_signal', 'MACD_hist', 'volume_MA20', 'volume_ratio',
        'HL_range_pct', 'CO_ratio', 'position_in_range'
    ]
    
    # Создание предиктора
    predictor = StockPredictor(
        model_path=MODEL_DIR / 'model_xgboost.joblib',
        feature_columns=feature_columns,
        include_macro=False  # Можно включить True для РФ рынка
    )
    
    # Пример прогноза
    from data_loader import DataLoader
    
    DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    loader = DataLoader(DATA_DIR)
    tickers_data = loader.process_all()
    
    # Прогноз для первой акции
    ticker = list(tickers_data.keys())[0]
    data = tickers_data[ticker]
    
    print("=" * 70)
    print("🔮 ПРОГНОЗ ДЛЯ АКЦИИ")
    print("=" * 70)
    print()
    
    report = predictor.predict(data, ticker)
    predictor._print_report(report) if hasattr(predictor, '_print_report') else print(report['report_text'])

"""
Prediction API для ML-модуля

Использование:
1. Пользователь вводит тикер (SBER, GAZP, AAPL)
2. yfinance подтягивает текущие данные (1 запрос!)
3. Модель даёт прогноз
4. AI-отчёт пользователю
"""

import sys
import io
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
import joblib
from datetime import datetime
from typing import Dict, Optional

# Устанавливаем UTF-8 кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / 'ml_module' / 'src'))

from features import FeatureEngineer


class StockPredictorAPI:
    """API для предсказания роста акций"""
    
    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: путь к обученной модели
        """
        if model_path is None:
            # Используем ФИНАЛЬНУЮ модель с реальными данными (шкала -100 до +100)
            model_path = Path(__file__).parent / 'ml_module' / 'models' / 'trained' / 'model_real_final.joblib'
        
        self.model_path = Path(model_path)
        self.model = None
        self.feature_columns = None
        self.metrics = None

        # Загрузка модели
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели и метрик"""
        if not self.model_path.exists():
            print(f"⚠️ Модель не найдена: {self.model_path}")
            print("   Сначала обучите модель: python train_quick_stable.py")
            return

        print(f"📥 Загрузка модели из {self.model_path}...")
        self.model = joblib.load(self.model_path)

        # Загрузка метрик
        metrics_path = self.model_path.parent / 'metrics_moex_quick.json'
        if metrics_path.exists():
            import json
            with open(metrics_path, 'r') as f:
                self.metrics = json.load(f)
            print(f"✅ Модель загружена! Accuracy: {self.metrics.get('accuracy', 'N/A'):.2%}")
            print(f"✅ ROC-AUC: {self.metrics.get('roc_auc', 'N/A'):.2%}")
        else:
            print("✅ Модель загружена!")

        # Определение колонок (технические + макро)
        self.feature_columns = [
            # Технические
            'open', 'high', 'low', 'close', 'volume',
            'MA20', 'MA50', 'MA200',
            'close_MA20_ratio', 'close_MA50_ratio', 'close_MA200_ratio',
            'daily_return', 'volatility_30', 'momentum_10_ratio',
            'RSI', 'MACD', 'MACD_signal', 'MACD_hist',
            'volume_MA20', 'volume_ratio',
            'HL_range_pct', 'CO_ratio', 'position_in_range',
            # Макро
            'key_rate', 'usd_rub', 'oil_price',
            'usd_rub_lag1', 'usd_rub_lag7',
            'key_rate_lag1', 'oil_price_lag1',
        ]
    
    def get_yfinance_data(self, ticker: str, period: str = '2y') -> Optional[pd.DataFrame]:
        """
        Загрузка данных из Yahoo Finance

        Args:
            ticker: тикер акции (SBER.ME, GAZP.ME, AAPL)
            period: период данных ('1mo', '3mo', '6mo', '1y', '2y', '5y')

        Returns:
            DataFrame с данными
        """
        try:
            print(f"   📥 Загрузка данных {ticker} из Yahoo Finance (период: {period})...")

            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if len(df) == 0:
                print(f"   ❌ Нет данных для {ticker}")
                print(f"   💡 Загрузите CSV с TradingEconomics или Мосбиржи")
                return None

            # Преобразование формата
            df = df.reset_index()
            df['Date'] = df['Date'].dt.date
            
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            df['Name'] = ticker.replace('.ME', '')

            print(f"   ✅ Загружено {len(df)} строк")

            return df

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return None

    def predict(self, ticker: str, use_yfinance: bool = True,
                user_csv_path: str = None) -> Dict:
        """
        Предсказание для акции
        
        Args:
            ticker: тикер акции
            use_yfinance: загружать ли из Yahoo Finance
            user_csv_path: путь к CSV файлу пользователя (приоритет)
        
        Returns:
            Dict с прогнозом
        """
        print("=" * 80)
        print(f"🔮 ПРОГНОЗ ДЛЯ: {ticker}")
        print("=" * 80)
        print()
        
        # Проверка модели
        if self.model is None:
            return {'error': 'Модель не загружена!'}
        
        # Загрузка данных
        df = None
        
        # Приоритет: CSV пользователя > Yahoo Finance
        if user_csv_path:
            print("📥 Загрузка данных пользователя (CSV)...")
            try:
                from user_data_loader import UserDataLoader
                loader = UserDataLoader()
                df = loader.load_csv(user_csv_path, ticker=ticker)
                
                # Загрузка макро данных
                df = loader.load_macro_data()
                
                print("   ✅ Данные пользователя загружены")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                return {'error': f'Не удалось загрузить CSV: {e}'}
        elif use_yfinance:
            df = self.get_yfinance_data(ticker, period='2y')
        else:
            df = None
        
        if df is None or len(df) < 30:
            return {'error': 'Недостаточно данных для прогноза (минимум 30 дней). Рекомендуется 60+ дней для большей точности.'}
        
        # Загрузка АКТУАЛЬНЫХ макро данных
        print()
        print("   📥 Загрузка АКТУАЛЬНЫХ макро данных...")

        try:
            from load_macro_current import get_current_macro
            
            # Получаем текущие макро данные
            macro_current = get_current_macro()
            
            # Добавляем в DataFrame последнюю строку
            last_date = df['date'].max()
            
            # Создаём строку с макро данными
            macro_row = pd.DataFrame([{
                'date': last_date,
                'key_rate': macro_current['key_rate'],
                'usd_rub': macro_current['usd_rub'],
                'inflation': macro_current['inflation'],
                'oil_price': macro_current['oil_price']
            }])
            
            # Добавляем макро признаки ко всем строкам (ffill)
            for col in ['key_rate', 'usd_rub', 'inflation', 'oil_price']:
                if col not in df.columns:
                    df[col] = macro_current[col]
            
            print(f"   ✅ Макро данные загружены:")
            print(f"      • Ключевая ставка: {macro_current['key_rate']:.2f}%")
            print(f"      • USD/RUB: {macro_current['usd_rub']:.2f}")
            print(f"      • Инфляция: {macro_current['inflation']:.2f}%")
            print(f"      • Нефть Brent: ${macro_current['oil_price']:.2f}")
            
        except Exception as e:
            print(f"   ⚠️ Макро данные не загружены: {e}")
            print(f"   ⚠️ Используем значения по умолчанию")
        
        # Создание признаков
        print()
        print("   📊 Расчёт признаков...")
        
        fe = FeatureEngineer({ticker: df})
        processed = fe.process_all()
        
        # Получение последних данных
        ticker_data = list(processed.values())[0]
        ticker_data = ticker_data.dropna()
        
        if len(ticker_data) < 10:
            return {'error': 'Недостаточно данных после расчёта индикаторов'}
        
        # Последние данные для предсказания
        latest = ticker_data.iloc[-1:]
        
        # Подготовка признаков
        available_cols = [c for c in self.feature_columns if c in latest.columns]
        X = latest[available_cols]
        
        # Предсказание
        print("   🤖 Генерация прогноза...")

        # Проверяем данные перед предсказанием
        print(f"   📊 X shape: {X.shape}")
        print(f"   📊 X columns: {list(X.columns)}")

        prediction = self.model.predict(X)[0]
        proba_raw = self.model.predict_proba(X)[0]

        print(f"   📊 predict_proba raw: {proba_raw}")
        print(f"   📊 predict_proba sum: {sum(proba_raw):.4f}")

        # Нормализуем вероятности чтобы сумма была 1
        # Это нужно т.к. XGBoost может выдавать некорректные proba на новых данных
        proba_sum = sum(proba_raw)
        if proba_sum > 0:
            probability = proba_raw[1] / proba_sum
        else:
            probability = 0.5

        # Преобразование в шкалу -100 до +100
        # probability=0.0 → score=-100 (уверенное падение)
        # probability=0.5 → score=0 (неопределенность)
        # probability=1.0 → score=+100 (уверенный рост)
        score = (probability - 0.5) * 200

        print(f"   📊 probability: {probability*100:.1f}%")
        print(f"   📊 score (-100 до +100): {score:.1f}")
        print(f"   ✅ Прогноз: {score:.1f}")

        # Формирование отчёта
        report = self._generate_report(ticker, prediction, probability, latest, score)

        return report
    
    def _generate_report(self, ticker: str, prediction: int, probability: float, 
                         latest: pd.DataFrame, score: float = None) -> Dict:
        """Генерация AI-отчёта"""

        # Определение рекомендации на основе score (-100 до +100)
        if score is None:
            score = (probability - 0.5) * 200
        
        if score >= 30:
            recommendation = "ПОКУПАТЬ"
            rec_color = "🟢"
        elif score <= -30:
            recommendation = "ПРОДАВАТЬ"
            rec_color = "🔴"
        else:
            recommendation = "ДЕРЖАТЬ"
            rec_color = "🟡"
        
        # Текущая цена
        current_price = latest['close'].values[0]
        
        # Анализ факторов
        factors = self._analyze_factors(latest)
        
        # Формирование отчёта
        report = {
            'ticker': ticker,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': current_price,
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability': probability,  # 0-1
            'score': score,  # -100 до +100
            'recommendation': recommendation,
            'factors': factors,
            'model_metrics': self.metrics
        }
        
        # Текстовый отчёт
        report['text_report'] = f"""
╔═══════════════════════════════════════════════════════════╗
║  📈 AI-ПРОГНОЗ: {ticker:<40} ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  {rec_color} {recommendation:<10} Вероятность роста (30 дней): {probability*100:.1f}%                   
║                                                           ║
║  Текущая цена: ${current_price:.2f}                                           ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  📊 ФАКТОРЫ:                                              ║
╚═══════════════════════════════════════════════════════════╝
"""
        
        if factors['positive']:
            report['text_report'] += "\n  ✅ Положительные:\n"
            for factor in factors['positive']:
                report['text_report'] += f"     • {factor}\n"
        
        if factors['negative']:
            report['text_report'] += "\n  ❌ Отрицательные:\n"
            for factor in factors['negative']:
                report['text_report'] += f"     • {factor}\n"
        
        if factors['neutral']:
            report['text_report'] += "\n  ⚪ Нейтральные:\n"
            for factor in factors['neutral']:
                report['text_report'] += f"     • {factor}\n"
        
        report['text_report'] += f"""
╠═══════════════════════════════════════════════════════════╣
║  ⚠️  РИСКИ:                                               ║
╚═══════════════════════════════════════════════════════════╝
     • Модель не является инвестиционной рекомендацией
     • Прошлые результаты не гарантируют будущую доходность
     • Проведите собственный анализ перед инвестированием

═══════════════════════════════════════════════════════════
"""
        
        return report
    
    def _analyze_factors(self, latest: pd.DataFrame) -> Dict:
        """Анализ факторов (расширенный)"""
        factors = {
            'positive': [],
            'negative': [],
            'neutral': []
        }

        # Технические индикаторы
        if 'RSI' in latest.columns:
            rsi = latest['RSI'].values[0]
            if rsi < 30:
                factors['positive'].append(f"RSI в зоне перепроданности ({rsi:.1f}) — возможен отскок")
            elif rsi > 70:
                factors['negative'].append(f"RSI в зоне перекупленности ({rsi:.1f}) — возможна коррекция")
            else:
                factors['neutral'].append(f"RSI в нейтральной зоне ({rsi:.1f})")

        if 'MACD' in latest.columns and 'MACD_signal' in latest.columns:
            macd = latest['MACD'].values[0]
            signal = latest['MACD_signal'].values[0]
            if macd > signal:
                factors['positive'].append(f"Бычий MACD (MACD выше Signal: {macd:.2f} > {signal:.2f})")
            else:
                factors['negative'].append(f"Медвежий MACD (MACD ниже Signal: {macd:.2f} < {signal:.2f})")

        if 'MA20' in latest.columns and 'MA50' in latest.columns:
            ma20 = latest['MA20'].values[0]
            ma50 = latest['MA50'].values[0]
            close = latest['close'].values[0]
            
            if close > ma20 > ma50:
                factors['positive'].append(f"Восходящий тренд (цена > MA20 > MA50)")
            elif close < ma20 < ma50:
                factors['negative'].append(f"Нисходящий тренд (цена < MA20 < MA50)")
            else:
                factors['neutral'].append(f"Боковой тренд (смешанные сигналы)")

        if 'volatility_30' in latest.columns:
            vol = latest['volatility_30'].values[0]
            if vol > 0.05:
                factors['negative'].append(f"Высокая волатильность ({vol*100:.1f}% за 30 дней)")
            elif vol < 0.02:
                factors['positive'].append(f"Низкая волатильность ({vol*100:.1f}% за 30 дней)")
            else:
                factors['neutral'].append(f"Умеренная волатильность ({vol*100:.1f}% за 30 дней)")

        if 'momentum_10_ratio' in latest.columns:
            momentum = latest['momentum_10_ratio'].values[0]
            if momentum > 0.05:
                factors['positive'].append(f"Сильный положительный импульс (+{momentum*100:.1f}% за 10 дней)")
            elif momentum < -0.05:
                factors['negative'].append(f"Отрицательный импульс ({momentum*100:.1f}% за 10 дней)")
            else:
                factors['neutral'].append(f"Слабый импульс ({momentum*100:.1f}% за 10 дней)")

        # Макро факторы
        if 'key_rate' in latest.columns:
            key_rate = latest['key_rate'].values[0]
            if key_rate > 15:
                factors['negative'].append(f"Высокая ключевая ставка ({key_rate:.2f}%) — давление на рынок")
            elif key_rate < 8:
                factors['positive'].append(f"Низкая ключевая ставка ({key_rate:.2f}%) — поддержка рынка")
            else:
                factors['neutral'].append(f"Ключевая ставка на умеренном уровне ({key_rate:.2f}%)")

        if 'usd_rub' in latest.columns:
            usd_rub = latest['usd_rub'].values[0]
            if 'usd_rub_lag1' in latest.columns:
                prev_usd = latest['usd_rub_lag1'].values[0]
                change = ((usd_rub - prev_usd) / prev_usd) * 100
                if change > 2:
                    factors['negative'].append(f"Рубль ослаб к доллару на {change:.1f}%")
                elif change < -2:
                    factors['positive'].append(f"Рубль укрепился к доллару на {abs(change):.1f}%")
                else:
                    factors['neutral'].append(f"Курс стабильный ({usd_rub:.2f} RUB/USD)")

        if 'oil_price' in latest.columns:
            oil = latest['oil_price'].values[0]
            if oil > 90:
                factors['positive'].append(f"Высокая цена нефти (${oil:.2f}/баррель) — поддержка экспортеров")
            elif oil < 60:
                factors['negative'].append(f"Низкая цена нефти (${oil:.2f}/баррель) — давление на экспорт")
            else:
                factors['neutral'].append(f"Цена нефти в норме (${oil:.2f}/баррель)")

        # Объемы
        if 'volume_ratio' in latest.columns:
            vol_ratio = latest['volume_ratio'].values[0]
            if vol_ratio > 1.5:
                factors['positive'].append(f"Высокий объем торгов (+{vol_ratio*100:.0f}% к среднему)")
            elif vol_ratio < 0.5:
                factors['negative'].append(f"Низкий объем торгов ({vol_ratio*100:.0f}% от среднего)")

        return factors

    def print_report(self, report: Dict):
        """Печать отчёта"""
        if 'error' in report:
            print(f"❌ Ошибка: {report['error']}")
            return
        
        print(report['text_report'])


if __name__ == "__main__":
    # Тест API
    print("=" * 80)
    print("🧪 ТЕСТ PREDICTION API")
    print("=" * 80)
    print()
    
    # Создание API
    api = StockPredictorAPI()
    
    if api.model is None:
        print()
        print("⚠️ Модель не загружена!")
        print("   Сначала обучите модель: python train_moex_full.py")
    else:
        # Тест на разных тикерах
        test_tickers = ['SBER.ME', 'GAZP.ME', 'LKOH.ME']
        
        for ticker in test_tickers:
            print()
            report = api.predict(ticker, use_yfinance=True)
            api.print_report(report)
            
            if ticker != test_tickers[-1]:
                print("\n\n")

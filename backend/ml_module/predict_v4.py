"""
INVESTEDU ML MODEL v4.0 — ПРОГНОЗЫ

Максимально точная модель с объяснениями

Использование:
    predictor = StockPredictorV4()
    result = predictor.predict('SBER', csv_path='data.csv')
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent))

# ✅ ИМПОРТ FeaturePipeline и DataValidator
from train_ultimate_v4 import FeaturePipeline, DataValidator

# ✅ КОСТЫЛЬ: Регистрируем классы в __main__ для загрузки старых моделей
# Модели сохранённые из "__main__" ищут классы там
import __main__
if not hasattr(__main__, 'FeaturePipeline'):
    __main__.FeaturePipeline = FeaturePipeline
if not hasattr(__main__, 'DataValidator'):
    __main__.DataValidator = DataValidator


class StockPredictorV4:
    """Продвинутый предиктор v4.0"""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Поиск последней модели
            model_dir = Path(__file__).parent / 'models' / 'trained'
            model_files = list(model_dir.glob('model_ultimate_v4_*.joblib'))
            
            if model_files:
                model_path = sorted(model_files)[-1]  # Последняя версия
            else:
                model_path = model_dir / 'model_ultimate_v4.joblib'
        
        self.model_path = Path(model_path)
        self.model = None
        self.feature_pipelines = {}
        self.metrics = {}
        self.feature_importance = {}
        self.horizons = []
        
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели"""
        if not self.model_path.exists():
            print(f"⚠️ Модель не найдена: {self.model_path}")
            print("   Обучите: python ml_module/train_ultimate_v4.py")
            return
        
        print(f"📥 Загрузка модели из {self.model_path}...")
        model_data = joblib.load(self.model_path)
        
        self.models = model_data['models']
        self.feature_pipelines = model_data['feature_pipelines']
        self.metrics = model_data['metrics']
        self.feature_importance = model_data['feature_importance']
        self.horizons = model_data.get('config', {}).get('horizons', [7, 30, 90])
        
        print(f"✅ Модель загружена!")
        print(f"   Горизонты: {self.horizons}")
        
        for horizon in self.horizons:
            if str(horizon) in self.metrics or horizon in self.metrics:
                h_key = str(horizon) if str(horizon) in self.metrics else horizon
                roc_auc = self.metrics[h_key].get('roc_auc', 'N/A')
                if isinstance(roc_auc, (int, float)):
                    print(f"   Горизонт {horizon} дней: ROC-AUC = {roc_auc:.4f}")
    
    def predict(self, ticker: str, csv_path: str = None, data: pd.DataFrame = None) -> Dict:
        """
        Прогноз для акции

        Args:
            ticker: тикер акции
            csv_path: путь к CSV файлу
            data: DataFrame с данными

        Returns:
            Dict с прогнозом и объяснениями
        """
        print("\n" + "=" * 80)
        print(f"🔮 ПРОГНОЗ ДЛЯ: {ticker}")
        print("=" * 80)

        # Проверка модели
        if self.models is None:
            return {'error': 'Модель не загружена!'}

        # Загрузка данных
        if data is None and csv_path:
            print(f"\n📥 Загрузка данных из {csv_path}...")

            # ✅ ИСПОЛЬЗУЕМ pandas read_csv с правильными параметрами
            try:
                # Пробуем разные кодировки
                df = None
                for encoding in ['utf-8', 'cp1251', 'latin1', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(
                            csv_path,
                            encoding=encoding,
                            quotechar='"',
                            skipinitialspace=True
                        )
                        print(f"   ✅ Кодировка: {encoding}")
                        break
                    except (UnicodeDecodeError, Exception):
                        continue

                if df is None:
                    # Последняя попытка с игнорированием ошибок
                    df = pd.read_csv(
                        csv_path,
                        encoding='utf-8',
                        errors='ignore',
                        quotechar='"',
                        skipinitialspace=True
                    )
                    print(f"   ⚠️ Кодировка: utf-8 с игнорированием ошибок")

                print(f"   ✅ Загружено {len(df)} строк")
                print(f"   📋 Колонки: {list(df.columns)}")

                # Нормализация имён колонок (только trim и lower)
                df.columns = df.columns.str.strip().str.lower()
                print(f"   📋 После нормализации: {list(df.columns)}")

                # Переименование колонок для поддержки разных форматов
                rename_map = {}
                # Date
                if 'datetime' in df.columns:
                    rename_map['datetime'] = 'date'
                # Price → Close
                if 'price' in df.columns:
                    rename_map['price'] = 'close'
                # Vol. → Volume (с точкой и без)
                if 'vol.' in df.columns:
                    rename_map['vol.'] = 'volume'
                elif 'vol' in df.columns:
                    rename_map['vol'] = 'volume'
                
                if rename_map:
                    df = df.rename(columns=rename_map)
                    print(f"   ✅ Переименованы колонки: {rename_map}")
                    print(f"   📋 После переименования: {list(df.columns)}")

                # Преобразование объёма (обработка "11.32M")
                if 'volume' in df.columns:
                    def parse_volume(x):
                        s = str(x).upper().strip().replace(',', '')
                        if 'B' in s:
                            return float(s.replace('B', '')) * 1_000_000_000
                        elif 'M' in s:
                            return float(s.replace('M', '')) * 1_000_000
                        elif 'K' in s:
                            return float(s.replace('K', '')) * 1_000
                        else:
                            try:
                                return float(s)
                            except:
                                return 0.0
                    df['volume'] = df['volume'].apply(parse_volume)

                # Преобразование Change %
                if 'change %' in df.columns:
                    df['change %'] = df['change %'].astype(str).str.replace('%', '').astype(float)

                # Преобразование даты (поддержка разных форматов)
                if 'date' in df.columns:
                    for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%d.%m.%Y', '%d %b %Y']:
                        try:
                            df['date'] = pd.to_datetime(df['date'], format=date_format)
                            print(f"   ✅ Формат даты: {date_format}")
                            break
                        except:
                            continue
                    else:
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')

                # Преобразование числовых колонок
                for col in ['open', 'high', 'low', 'close']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # Добавляем тикер
                if 'Name' not in df.columns:
                    df['Name'] = ticker

                data = df
                print(f"   ✅ DataFrame создан: {len(data)} строк, {len(data.columns)} колонок")
                print(f"   ✅ Колонки: {list(data.columns)}")
                
                # 🔍 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ПЕРЕД ВАЛИДАЦИЕЙ
                print(f"\n🔍 ПРОВЕРКА КОЛОНОК ПЕРЕД ВАЛИДАЦИЕЙ:")
                required = ['date', 'open', 'high', 'low', 'close', 'volume']
                for col in required:
                    exists = col in data.columns
                    print(f"   {col}: {'✅' if exists else '❌'} (в наличии: {list(data.columns)})")

            except Exception as e:
                print(f"   ❌ Ошибка парсинга: {e}")
                import traceback
                traceback.print_exc()
                return {'error': f'Не удалось прочитать CSV: {e}'}

        elif data is None:
            return {'error': 'Нет данных для прогноза!'}

        # Валидация
        print("\n🔍 Валидация данных...")
        is_valid, errors, warnings_list = DataValidator.validate(data)

        if not is_valid:
            return {'error': f'Валидация не пройдена: {errors}'}

        for warning in warnings_list:
            print(f"⚠️ {warning}")

        # Очистка
        data = DataValidator.clean(data)
        print(f"✅ Загружено {len(data):,} строк")
        
        # Предсказания для каждого горизонта
        print("\n🤖 Генерация прогнозов...")
        
        predictions = {}
        for horizon in self.horizons:
            h_key = str(horizon) if str(horizon) in self.models else horizon
            
            if h_key not in self.models:
                continue
            
            model = self.models[h_key]
            pipeline = self.feature_pipelines[h_key]
            
            # Создание признаков
            df_features = pipeline.create_all_features(data.copy())
            
            # Последние данные
            latest = df_features.iloc[-1:].copy()
            
            # Проверка признаков
            missing = set(pipeline.feature_columns) - set(latest.columns)
            for col in missing:
                latest[col] = 0
            
            X = latest[pipeline.feature_columns].fillna(0)
            
            # Предсказание
            pred = model.predict(X.values)[0]
            proba = model.predict_proba(X.values)[0, 1]
            
            predictions[horizon] = {
                'prediction': pred,
                'probability': proba,
                'recommendation': 'ПОКУПАТЬ' if proba >= 0.6 else 'ПРОДАВАТЬ' if proba <= 0.4 else 'ДЕРЖАТЬ'
            }
            
            print(f"   {horizon} дней: {'ПОКУПАТЬ' if pred == 1 else 'ПРОДАВАТЬ'} ({proba*100:.1f}%)")
        
        # Объединённый прогноз
        if predictions:
            avg_proba = np.mean([p['probability'] for p in predictions.values()])
            combined_pred = 1 if avg_proba >= 0.6 else 0 if avg_proba <= 0.4 else -1
            
            combined_rec = 'ПОКУПАТЬ' if combined_pred == 1 else 'ПРОДАВАТЬ' if combined_pred == 0 else 'ДЕРЖАТЬ'
        else:
            avg_proba = 0.5
            combined_rec = 'НЕИЗВЕСТНО'
        
        # SHAP объяснения
        print("\n🔍 Объяснение прогноза...")
        shap_explanation = self._explain_prediction(data, predictions)
        
        # Формирование отчёта
        report = self._generate_report(
            ticker=ticker,
            predictions=predictions,
            combined_probability=avg_proba,
            combined_recommendation=combined_rec,
            current_price=data['close'].iloc[-1],
            shap_explanation=shap_explanation
        )
        
        return report
    
    def _explain_prediction(self, data: pd.DataFrame, predictions: Dict) -> Dict:
        """Объяснение прогноза"""
        positive = []
        negative = []
        
        # RSI
        if 'rsi_14' in data.columns:
            rsi = data['rsi_14'].iloc[-1]
            if pd.notna(rsi):
                if rsi < 30:
                    positive.append({'feature': 'RSI', 'value': f'{rsi:.1f}', 'impact': 'Перепроданность'})
                elif rsi > 70:
                    negative.append({'feature': 'RSI', 'value': f'{rsi:.1f}', 'impact': 'Перекупленность'})
        
        # MACD
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd = data['macd'].iloc[-1]
            signal = data['macd_signal'].iloc[-1]
            if pd.notna(macd) and pd.notna(signal):
                if macd > signal:
                    positive.append({'feature': 'MACD', 'value': f'{macd:.2f} > {signal:.2f}', 'impact': 'Бычий сигнал'})
                else:
                    negative.append({'feature': 'MACD', 'value': f'{macd:.2f} < {signal:.2f}', 'impact': 'Медвежий сигнал'})
        
        # Тренд
        if 'ma50_above_ma200' in data.columns:
            if data['ma50_above_ma200'].iloc[-1] == 1:
                positive.append({'feature': 'Тренд', 'value': 'Восходящий', 'impact': 'MA50 > MA200'})
            else:
                negative.append({'feature': 'Тренд', 'value': 'Нисходящий', 'impact': 'MA50 < MA200'})
        
        # Волатильность
        if 'volatility_20d' in data.columns:
            vol = data['volatility_20d'].iloc[-1]
            if pd.notna(vol):
                if vol > 0.05:
                    negative.append({'feature': 'Волатильность', 'value': f'{vol*100:.1f}%', 'impact': 'Высокая'})
                else:
                    positive.append({'feature': 'Волатильность', 'value': f'{vol*100:.1f}%', 'impact': 'Нормальная'})
        
        # Объём
        if 'volume_ratio' in data.columns:
            vol_ratio = data['volume_ratio'].iloc[-1]
            if pd.notna(vol_ratio):
                if vol_ratio > 1.5:
                    positive.append({'feature': 'Объём', 'value': f'{vol_ratio:.1f}x', 'impact': 'Выше среднего'})
                elif vol_ratio < 0.5:
                    negative.append({'feature': 'Объём', 'value': f'{vol_ratio:.1f}x', 'impact': 'Ниже среднего'})
        
        # Возврат
        if 'return_10d' in data.columns:
            ret = data['return_10d'].iloc[-1]
            if pd.notna(ret):
                if ret > 0.1:
                    positive.append({'feature': 'Доходность 10д', 'value': f'{ret*100:.1f}%', 'impact': 'Сильный рост'})
                elif ret < -0.1:
                    negative.append({'feature': 'Доходность 10д', 'value': f'{ret*100:.1f}%', 'impact': 'Сильное падение'})
        
        return {
            'positive': positive,
            'negative': negative,
            'method': 'Эвристика + Feature Importance'
        }
    
    def _generate_report(self, ticker: str, predictions: Dict, 
                        combined_probability: float, combined_recommendation: str,
                        current_price: float, shap_explanation: Dict) -> Dict:
        """Генерация отчёта"""
        
        # Текстовый отчёт
        report_text = f"""
╔═══════════════════════════════════════════════════════════╗
║  📈 AI-ПРОГНОЗ v4.0: {ticker:<32} ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  {('🟢' if combined_recommendation == 'ПОКУПАТЬ' else '🔴' if combined_recommendation == 'ПРОДАВАТЬ' else '🟡')} {combined_recommendation:<10} Вероятность: {combined_probability*100:.1f}%
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  ГОРИЗОНТЫ:                                               ║
╠═══════════════════════════════════════════════════════════╣
"""
        
        for horizon, pred in sorted(predictions.items()):
            rec_icon = '🟢' if pred['recommendation'] == 'ПОКУПАТЬ' else '🔴' if pred['recommendation'] == 'ПРОДАВАТЬ' else '🟡'
            report_text += f"║  {horizon:>2} дней: {rec_icon} {pred['recommendation']:<8} ({pred['probability']*100:.1f}%){' ' * 18}║\n"
        
        report_text += f"""╠═══════════════════════════════════════════════════════════╣
║  ТЕКУЩАЯ ЦЕНА: ${current_price:.2f}                                          ║
╚═══════════════════════════════════════════════════════════╝

📊 ФАКТОРЫ:
"""
        
        if shap_explanation['positive']:
            report_text += "\n✅ Положительные:\n"
            for factor in shap_explanation['positive'][:5]:
                report_text += f"   • {factor['feature']}: {factor['value']} ({factor['impact']})\n"
        
        if shap_explanation['negative']:
            report_text += "\n❌ Отрицательные:\n"
            for factor in shap_explanation['negative'][:5]:
                report_text += f"   • {factor['feature']}: {factor['value']} ({factor['impact']})\n"
        
        if not shap_explanation['positive'] and not shap_explanation['negative']:
            report_text += "\n⚪ Нет явных факторов\n"
        
        report_text += f"""
═══════════════════════════════════════════════════════════
⚠️  ПРЕДУПРЕЖДЕНИЕ:
   • Это не инвестиционная рекомендация
   • Прошлые результаты не гарантируют будущую доходность
   • Точность модели: ~68-75% (ROC-AUC)
   • Проведите собственный анализ
═══════════════════════════════════════════════════════════
"""
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': current_price,
            'recommendation': combined_recommendation,
            'probability': combined_probability,
            'predictions': predictions,
            'report_text': report_text,
            'factors': shap_explanation,
            'metrics': self.metrics
        }
    
    def print_report(self, report: Dict):
        """Печать отчёта"""
        if 'error' in report:
            print(f"❌ Ошибка: {report['error']}")
            return
        
        print(report['report_text'])


if __name__ == "__main__":
    predictor = StockPredictorV4()
    
    if predictor.models is None:
        print("\n⚠️ Модель не загружена!")
        print("   Обучите: python ml_module/train_ultimate_v4.py")
    else:
        print("\n" + "=" * 80)
        print("ПРИМЕР ИСПОЛЬЗОВАНИЯ")
        print("=" * 80)
        
        test_csv = Path(__file__).parent.parent / 'ml_module' / 'Data' / 'moex' / 'SBER_D1.csv'
        
        if test_csv.exists():
            report = predictor.predict('SBER', csv_path=str(test_csv))
            predictor.print_report(report)
        else:
            print("\n⚠️ Нет тестового CSV")

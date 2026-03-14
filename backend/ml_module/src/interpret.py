"""
Этап 7: Интерпретация результатов (Feature Importance)
Этап 8: AI-анализ для пользователя

Анализ важности признаков и генерация текстового отчёта
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import joblib


class ModelInterpreter:
    """Интерпретация модели"""
    
    def __init__(self, model, feature_columns: List[str]):
        self.model = model
        self.feature_columns = feature_columns
        self.feature_importance = None
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Получение важности признаков"""
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        else:
            # Для sklearn моделей
            importance = self.model.feature_importances_
        
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importance
        }).sort_values('importance', ascending=False).reset_index(drop=True)
        
        return self.feature_importance
    
    def plot_importance(self, top_n: int = 15, output_dir: Path = None):
        """Визуализация важности признаков"""
        import matplotlib.pyplot as plt
        
        if self.feature_importance is None:
            self.get_feature_importance()
        
        top_features = self.feature_importance.head(top_n)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title('Feature Importance')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
            print(f"💾 Важность признаков сохранена в {output_dir / 'feature_importance.png'}")
        
        plt.close()
    
    def get_top_features(self, top_n: int = 10) -> List[str]:
        """Получить топ признаков"""
        if self.feature_importance is None:
            self.get_feature_importance()
        
        return self.feature_importance.head(top_n)['feature'].tolist()
    
    def print_importance(self):
        """Печать важности признаков"""
        if self.feature_importance is None:
            self.get_feature_importance()
        
        print("=" * 70)
        print("📊 ЭТАП 7: ИНТЕРПРЕТАЦИЯ МОДЕЛИ")
        print("=" * 70)
        print()
        
        print("🔝 Топ-15 важных признаков:")
        print()
        
        for i, row in self.feature_importance.head(15).iterrows():
            bar = '█' * int(row['importance'] * 100)
            print(f"   {row['feature']:<25} {bar} {row['importance']:.4f}")
        
        print()
        print("=" * 70)
        print("✅ ЭТАП 7 ЗАВЕРШЁН")
        print("=" * 70)
        print()


class AIAnalyzer:
    """AI-анализ для пользователя"""
    
    def __init__(self, model, feature_columns: List[str], interpreter: ModelInterpreter = None):
        self.model = model
        self.feature_columns = feature_columns
        self.interpreter = interpreter
    
    def analyze_stock(
        self, 
        ticker: str, 
        features: pd.DataFrame,
        macro_data: Dict = None
    ) -> Dict:
        """
        Анализ акции и генерация отчёта
        
        Args:
            ticker: тикер акции
            features: признаки для модели (один пример)
            macro_data: макроэкономические данные (опционально)
        """
        # Предсказание
        proba = self.model.predict_proba(features)[0, 1]
        prediction = self.model.predict(features)[0]
        
        # Анализ факторов
        factors = self._analyze_factors(features)
        
        # Генерация отчёта
        report = self._generate_report(ticker, proba, prediction, factors, macro_data)
        
        return report
    
    def _analyze_factors(self, features: pd.DataFrame) -> Dict:
        """Анализ факторов"""
        factors = {
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        # Получаем значения признаков
        feat = features.iloc[0] if isinstance(features, pd.DataFrame) else features
        
        # RSI анализ
        if 'RSI' in feat:
            rsi = feat['RSI']
            if rsi < 30:
                factors['positive'].append("RSI в зоне перепроданности")
            elif rsi > 70:
                factors['negative'].append("RSI в зоне перекупленности")
            else:
                factors['neutral'].append("RSI в нейтральной зоне")
        
        # MACD анализ
        if 'MACD' in feat and 'MACD_signal' in feat:
            if feat['MACD'] > feat['MACD_signal']:
                factors['positive'].append("Бычий MACD (MACD выше Signal)")
            else:
                factors['negative'].append("Медвежий MACD (MACD ниже Signal)")
        
        # Скользящие средние
        if 'close_MA50_ratio' in feat:
            if feat['close_MA50_ratio'] > 1.05:
                factors['positive'].append("Цена выше MA50 (восходящий тренд)")
            elif feat['close_MA50_ratio'] < 0.95:
                factors['negative'].append("Цена ниже MA50 (нисходящий тренд)")
            else:
                factors['neutral'].append("Цена около MA50 (боковик)")
        
        if 'close_MA200_ratio' in feat:
            if feat['close_MA200_ratio'] > 1.1:
                factors['positive'].append("Цена выше MA200 (долгосрочный рост)")
            elif feat['close_MA200_ratio'] < 0.9:
                factors['negative'].append("Цена ниже MA200 (долгосрочное падение)")
        
        # Momentum
        if 'momentum_10_ratio' in feat:
            if feat['momentum_10_ratio'] > 0.05:
                factors['positive'].append("Положительный momentum (+5% за 10 дней)")
            elif feat['momentum_10_ratio'] < -0.05:
                factors['negative'].append("Отрицательный momentum (-5% за 10 дней)")
        
        # Volatility
        if 'volatility_30' in feat:
            vol = feat['volatility_30']
            if vol > 0.03:
                factors['negative'].append("Высокая волатильность")
            elif vol < 0.01:
                factors['neutral'].append("Низкая волатильность")
        
        # Volume
        if 'volume_ratio' in feat:
            if feat['volume_ratio'] > 1.5:
                factors['positive'].append("Рост объёма торгов")
            elif feat['volume_ratio'] < 0.5:
                factors['negative'].append("Падение объёма торгов")
        
        return factors
    
    def _generate_report(
        self,
        ticker: str,
        proba: float,
        prediction: int,
        factors: Dict,
        macro_data: Dict = None
    ) -> Dict:
        """Генерация текстового отчёта"""
        
        # Вероятность роста
        prob_growth = proba * 100
        
        # Рекомендация
        if prob_growth >= 65:
            recommendation = "ПОКУПАТЬ"
            rec_color = "🟢"
        elif prob_growth >= 50:
            recommendation = "ДЕРЖАТЬ"
            rec_color = "🟡"
        else:
            recommendation = "ПРОДАВАТЬ"
            rec_color = "🔴"
        
        # Формирование текста
        report_text = f"""
╔═══════════════════════════════════════════════════════════╗
║  📈 AI-АНАЛИЗ: {ticker:<42} ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  {rec_color} {recommendation:<10} Вероятность роста (30 дней): {prob_growth:.1f}%                   
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  📊 ФАКТОРЫ:                                              ║
╚═══════════════════════════════════════════════════════════╝
"""
        
        # Положительные факторы
        if factors['positive']:
            report_text += "\n  ✅ Положительные:\n"
            for factor in factors['positive']:
                report_text += f"     • {factor}\n"
        
        # Отрицательные факторы
        if factors['negative']:
            report_text += "\n  ❌ Отрицательные:\n"
            for factor in factors['negative']:
                report_text += f"     • {factor}\n"
        
        # Нейтральные
        if factors['neutral']:
            report_text += "\n  ⚪ Нейтральные:\n"
            for factor in factors['neutral']:
                report_text += f"     • {factor}\n"
        
        # Макро данные
        if macro_data:
            report_text += "\n╠═══════════════════════════════════════════════════════════╣\n"
            report_text += "║  🌍 МАКРОЭКОНОМИКА:                                         ║\n"
            report_text += "╚═══════════════════════════════════════════════════════════╝\n"
            
            if 'key_rate' in macro_data:
                report_text += f"     • Ключевая ставка: {macro_data['key_rate']:.2f}%\n"
            if 'usd_rub' in macro_data:
                report_text += f"     • USD/RUB: {macro_data['usd_rub']:.2f}\n"
            if 'oil_price' in macro_data:
                report_text += f"     • Нефть Brent: ${macro_data['oil_price']:.2f}\n"
        
        # Риски
        report_text += """
╠═══════════════════════════════════════════════════════════╣
║  ⚠️  РИСКИ:                                               ║
╚═══════════════════════════════════════════════════════════╝
     • Модель не является инвестиционной рекомендацией
     • Прошлые результаты не гарантируют будущую доходность
     • Проведите собственный анализ перед инвестированием

═══════════════════════════════════════════════════════════
"""
        
        return {
            'ticker': ticker,
            'probability': prob_growth,
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'recommendation': recommendation,
            'factors': factors,
            'macro_data': macro_data,
            'report_text': report_text
        }
    
    def print_report(self, report: Dict):
        """Печать отчёта"""
        print(report['report_text'])


if __name__ == "__main__":
    from pathlib import Path
    
    # Загрузка модели
    MODEL_DIR = Path(__file__).parent.parent / "models" / "trained"
    model = joblib.load(MODEL_DIR / 'model_xgboost.joblib')
    
    # Загрузка метрик
    import json
    with open(MODEL_DIR / 'metrics.json') as f:
        metrics = json.load(f)
    
    # Пример анализа
    feature_columns = [
        'open', 'high', 'low', 'close', 'volume',
        'MA20', 'MA50', 'MA200', 'close_MA20_ratio', 'close_MA50_ratio',
        'close_MA200_ratio', 'daily_return', 'volatility_30', 'momentum_10_ratio',
        'RSI', 'MACD', 'MACD_signal', 'MACD_hist', 'volume_MA20', 'volume_ratio',
        'HL_range_pct', 'CO_ratio', 'position_in_range'
    ]
    
    # Создание интерпретатора
    interpreter = ModelInterpreter(model, feature_columns)
    interpreter.print_importance()
    
    # Сохранение важности
    OUTPUT_DIR = Path(__file__).parent.parent / "models" / "results"
    interpreter.plot_importance(top_n=15, output_dir=OUTPUT_DIR)
    
    # AI-анализатор
    analyzer = AIAnalyzer(model, feature_columns, interpreter)
    
    # Пример (фейковые данные для демонстрации)
    sample_features = pd.DataFrame([{
        'open': 150.0, 'high': 152.0, 'low': 149.0, 'close': 151.0,
        'volume': 1000000, 'MA20': 148.0, 'MA50': 145.0, 'MA200': 140.0,
        'close_MA20_ratio': 1.02, 'close_MA50_ratio': 1.04, 'close_MA200_ratio': 1.08,
        'daily_return': 0.01, 'volatility_30': 0.02, 'momentum_10_ratio': 0.03,
        'RSI': 55.0, 'MACD': 2.0, 'MACD_signal': 1.5, 'MACD_hist': 0.5,
        'volume_MA20': 900000, 'volume_ratio': 1.1, 'HL_range_pct': 0.02,
        'CO_ratio': 1.007, 'position_in_range': 0.67
    }])
    
    report = analyzer.analyze_stock('AAPL', sample_features)
    analyzer.print_report(report)

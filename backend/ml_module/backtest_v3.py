"""
INVESTEDU ML MODEL v3.0 — BACKTESTING

Профессиональный backtesting модели с реальными условиями:
- Комиссии (0.05%)
- Проскальзывание (0.1%)
- Walk-Forward валидация
- Метрики: CAGR, Sharpe, Sortino, Max Drawdown, Win Rate
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import warnings

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, roc_auc_score

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent))


class AdvancedBacktester:
    """
    Продвинутый backtesting с реальными условиями
    
    Условия:
    - Комиссия: 0.05%
    - Проскальзывание: 0.1%
    - Ребалансировка: по сигналу модели
    - Начальный капитал: 1,000,000 RUB
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000,
        commission: float = 0.0005,
        slippage: float = 0.001,
        position_size: float = 0.1
    ):
        """
        Args:
            initial_capital: начальный капитал
            commission: комиссия брокера (0.05%)
            slippage: проскальзывание (0.1%)
            position_size: размер позиции (10% от капитала)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
        
        self.results = {}
    
    def run(
        self,
        model,
        data: pd.DataFrame,
        feature_columns: List[str],
        horizon: int = 7,
        target_col: str = 'target_7d'
    ) -> Dict:
        """
        Запуск backtesting
        
        Args:
            model: обученная модель
            data: данные с признаками
            feature_columns: список признаков
            horizon: горизонт прогноза
            target_col: название колонки target
        
        Returns:
            Dict с метриками
        """
        print("\n" + "=" * 80)
        print("📈 BACKTESTING МОДЕЛИ")
        print("=" * 80)
        print(f"\nПараметры:")
        print(f"   Начальный капитал: {self.initial_capital:,.0f} RUB")
        print(f"   Комиссия: {self.commission*100:.2f}%")
        print(f"   Проскальзывание: {self.slippage*100:.2f}%")
        print(f"   Размер позиции: {self.position_size*100:.1f}%")
        print(f"   Горизонт: {horizon} дней")
        
        # Подготовка данных
        df = data.copy()
        df = df.dropna(subset=feature_columns + [target_col])
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"\n   Данные: {len(df):,} строк")
        print(f"   Период: {df['date'].min().date()} — {df['date'].max().date()}")
        
        # Симуляция торговли
        capital = self.initial_capital
        position = 0
        portfolio_values = []
        trades = []
        predictions = []
        
        print("\n Симуляция торговли...")
        
        for i in range(len(df) - horizon):
            row = df.iloc[i]
            future_row = df.iloc[i + horizon]
            
            # Получаем признаки
            X = row[feature_columns].fillna(0).values.reshape(1, -1)
            
            # Предсказание модели
            try:
                pred = model.predict(X)[0]
                proba = model.predict_proba(X)[0, 1]
            except:
                continue
            
            predictions.append({
                'date': row['date'],
                'prediction': pred,
                'probability': proba,
                'actual': future_row[target_col]
            })
            
            current_price = row['close']
            
            # Решение: BUY
            if pred == 1 and capital > 0:
                # Покупаем на 10% капитала
                buy_amount = capital * self.position_size
                shares = int(buy_amount / current_price)
                
                if shares > 0:
                    # Стоимость с комиссиями
                    cost = shares * current_price * (1 + self.commission + self.slippage)
                    actual_shares = int(cost / current_price)
                    
                    if actual_shares > 0:
                        capital -= actual_shares * current_price * (1 + self.commission + self.slippage)
                        position += actual_shares
                        
                        trades.append({
                            'type': 'buy',
                            'date': row['date'],
                            'price': current_price,
                            'shares': actual_shares,
                            'cost': actual_shares * current_price
                        })
            
            # Решение: SELL
            elif pred == 0 and position > 0:
                # Продаём всё
                revenue = position * current_price * (1 - self.commission - self.slippage)
                capital += revenue
                
                trades.append({
                    'type': 'sell',
                    'date': row['date'],
                    'price': current_price,
                    'shares': position,
                    'revenue': revenue
                })
                
                position = 0
            
            # Стоимость портфеля
            portfolio_value = capital + position * current_price
            portfolio_values.append({
                'date': row['date'],
                'value': portfolio_value,
                'capital': capital,
                'position': position * current_price
            })
        
        # Финальная продажа
        if position > 0 and len(df) > 0:
            final_price = df.iloc[-1]['close']
            revenue = position * final_price * (1 - self.commission - self.slippage)
            capital += revenue
            
            trades.append({
                'type': 'sell',
                'date': df.iloc[-1]['date'],
                'price': final_price,
                'shares': position,
                'revenue': revenue,
                'final': True
            })
        
        final_value = capital
        
        # Расчёт метрик
        print("\n📊 Расчёт метрик...")
        
        portfolio_df = pd.DataFrame(portfolio_values)
        trades_df = pd.DataFrame(trades)
        predictions_df = pd.DataFrame(predictions)
        
        # Метрики
        metrics = self._calculate_metrics(
            portfolio_values=portfolio_df['value'].tolist(),
            trades=trades,
            predictions=predictions,
            dates=portfolio_df['date'].tolist()
        )
        
        # Печать результатов
        self._print_results(metrics, trades_df, predictions_df)
        
        self.results = {
            'metrics': metrics,
            'trades': trades,
            'predictions': predictions,
            'portfolio_values': portfolio_values
        }
        
        return self.results
    
    def _calculate_metrics(
        self,
        portfolio_values: List[float],
        trades: List[Dict],
        predictions: List[Dict],
        dates: List[pd.Timestamp]
    ) -> Dict:
        """Расчёт метрик"""
        
        portfolio_series = pd.Series(portfolio_values)
        returns = portfolio_series.pct_change().dropna()
        
        # Длительность в годах
        if len(dates) > 1:
            duration_days = (dates[-1] - dates[0]).days
            duration_years = duration_days / 365.25
        else:
            duration_years = 1
        
        # Total Return
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital
        
        # CAGR
        if duration_years > 0:
            cagr = (portfolio_values[-1] / self.initial_capital) ** (1 / duration_years) - 1
        else:
            cagr = 0
        
        # Волатильность (annualized)
        volatility = returns.std() * np.sqrt(252)
        
        # Sharpe Ratio (безрисочная ставка 10%)
        risk_free_rate = 0.10
        if volatility > 0:
            sharpe_ratio = (cagr - risk_free_rate) / volatility
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino_ratio = (cagr - risk_free_rate) / downside_std if downside_std > 0 else 0
        else:
            sortino_ratio = 0
        
        # Max Drawdown
        cumulative = (portfolio_series / portfolio_series.cummax()).values
        max_drawdown = (1 - cumulative.min())
        
        # Win Rate
        if len(trades) > 0:
            buy_trades = [t for t in trades if t['type'] == 'buy']
            sell_trades = [t for t in trades if t['type'] == 'sell']
            
            # Считаем прибыльные сделки
            profitable_trades = 0
            for i, sell in enumerate(sell_trades):
                if i < len(buy_trades):
                    buy = buy_trades[i]
                    if sell.get('price', 0) > buy['price']:
                        profitable_trades += 1
            
            win_rate = profitable_trades / max(1, len(sell_trades))
        else:
            win_rate = 0
        
        # Profit Factor
        if len(trades) > 0:
            profits = []
            for i, sell in enumerate(sell_trades):
                if i < len(buy_trades):
                    buy = buy_trades[i]
                    pnl = (sell.get('price', 0) - buy['price']) * buy['shares']
                    profits.append(pnl)
            
            gross_profit = sum(p for p in profits if p > 0)
            gross_loss = abs(sum(p for p in profits if p < 0))
            profit_factor = gross_profit / max(1, gross_loss)
        else:
            profit_factor = 0
        
        # Accuracy прогнозов
        if len(predictions) > 0:
            y_true = [p['actual'] for p in predictions]
            y_pred = [p['prediction'] for p in predictions]
            accuracy = accuracy_score(y_true, y_pred)
            
            try:
                roc_auc = roc_auc_score(y_true, [p['probability'] for p in predictions])
            except:
                roc_auc = 0.5
        else:
            accuracy = 0
            roc_auc = 0.5
        
        # Количество сделок
        n_trades = len(trades)
        
        metrics = {
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'final_value': portfolio_values[-1],
            'cagr': cagr,
            'cagr_pct': cagr * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'profit_factor': profit_factor,
            'accuracy': accuracy,
            'accuracy_pct': accuracy * 100,
            'roc_auc': roc_auc,
            'n_trades': n_trades,
            'duration_days': duration_days,
            'duration_years': duration_years,
            'volatility': volatility,
            'volatility_pct': volatility * 100
        }
        
        return metrics
    
    def _print_results(self, metrics: Dict, trades_df: pd.DataFrame, predictions_df: pd.DataFrame):
        """Печать результатов"""
        
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ BACKTESTING")
        print("=" * 80)
        
        print(f"\n💰 ДОХОДНОСТЬ:")
        print(f"   Начальный капитал: {self.initial_capital:,.0f} RUB")
        print(f"   Финальный капитал: {metrics['final_value']:,.0f} RUB")
        print(f"   Общая доходность: {metrics['total_return_pct']:+.1f}%")
        print(f"   CAGR: {metrics['cagr_pct']:+.1f}% годовых")
        
        print(f"\n📈 РИСК-МЕТРИКИ:")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown_pct']:.1f}%")
        print(f"   Волатильность: {metrics['volatility_pct']:.1f}%")
        
        print(f"\n🎯 ТОЧНОСТЬ:")
        print(f"   Accuracy: {metrics['accuracy_pct']:.1f}%")
        print(f"   ROC-AUC: {metrics['roc_auc']:.3f}")
        print(f"   Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n📊 СДЕЛКИ:")
        print(f"   Количество: {metrics['n_trades']}")
        print(f"   Период: {metrics['duration_days']} дней ({metrics['duration_years']:.1f} лет)")
        
        # Оценка качества
        print("\n" + "=" * 80)
        print("📋 ОЦЕНКА КАЧЕСТВА МОДЕЛИ")
        print("=" * 80)
        
        score = 0
        max_score = 100
        
        # Sharpe Ratio (до 30 баллов)
        sharpe_score = min(30, metrics['sharpe_ratio'] * 15)
        score += sharpe_score
        
        # Accuracy (до 25 баллов)
        accuracy_score = min(25, (metrics['accuracy'] - 0.5) * 50)
        score += accuracy_score
        
        # Win Rate (до 20 баллов)
        win_score = min(20, metrics['win_rate'] * 40)
        score += win_score
        
        # Max Drawdown (до 15 баллов)
        dd_score = max(0, 15 - metrics['max_drawdown'] * 30)
        score += dd_score
        
        # Profit Factor (до 10 баллов)
        pf_score = min(10, metrics['profit_factor'] * 5)
        score += pf_score
        
        print(f"\n   Sharpe Ratio:      {sharpe_score:.1f}/{30}")
        print(f"   Accuracy:          {accuracy_score:.1f}/{25}")
        print(f"   Win Rate:          {win_score:.1f}/{20}")
        print(f"   Max Drawdown:      {dd_score:.1f}/{15}")
        print(f"   Profit Factor:     {pf_score:.1f}/{10}")
        print(f"   ───────────────────────")
        print(f"   ИТОГО:             {score:.1f}/{max_score}")
        
        # Вердикт
        print("\n" + "=" * 80)
        if score >= 80:
            print("✅ ОТЛИЧНО: Модель готова к реальному использованию!")
        elif score >= 60:
            print("✅ ХОРОШО: Модель работает, но есть куда улучшать.")
        elif score >= 40:
            print("⚠️ УДОВЛЕТВОРИТЕЛЬНО: Модель требует доработки.")
        else:
            print("❌ ПЛОХО: Модель не готова к использованию.")
        print("=" * 80)


class WalkForwardValidator:
    """
    Walk-Forward валидация
    
    Честная оценка модели на скользящем окне
    """
    
    def __init__(
        self,
        train_days: int = 365,
        test_days: int = 90,
        step_days: int = 30
    ):
        self.train_days = train_days
        self.test_days = test_days
        self.step_days = step_days
    
    def validate(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        model_class,
        target_col: str = 'target_7d'
    ) -> Dict:
        """
        Walk-Forward валидация
        
        Returns:
            Dict с метриками по всем фолдам
        """
        print("\n" + "=" * 80)
        print("🔄 WALK-FORWARD ВАЛИДАЦИЯ")
        print("=" * 80)
        print(f"\nПараметры:")
        print(f"   Train window: {self.train_days} дней")
        print(f"   Test window: {self.test_days} дней")
        print(f"   Step: {self.step_days} дней")
        
        data = data.copy()
        data = data.sort_values('date').reset_index(drop=True)
        
        # Генерация фолдов
        folds = []
        results = []
        
        for i in range(0, len(data) - self.train_days - self.test_days, self.step_days):
            train_start = i
            train_end = i + self.train_days
            test_end = train_end + self.test_days
            
            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[train_end:test_end]
            
            if len(train_data) < 100 or len(test_data) < 10:
                continue
            
            folds.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_end': test_end
            })
        
        print(f"\n   Количество фолдов: {len(folds)}")
        
        # Валидация по каждому фолду
        for i, fold in enumerate(folds, 1):
            print(f"\n📊 Fold {i}/{len(folds)}...")
            
            train_data = data.iloc[fold['train_start']:fold['train_end']]
            test_data = data.iloc[fold['train_end']:fold['test_end']]
            
            # Подготовка
            X_train = train_data[feature_columns].fillna(0)
            y_train = train_data[target_col]
            X_test = test_data[feature_columns].fillna(0)
            y_test = test_data[target_col]
            
            # Обучение
            try:
                model = model_class()
                model.fit(X_train.values, y_train.values)
                
                # Предсказание
                y_pred = model.predict(X_test.values)
                y_proba = model.predict_proba(X_test.values)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                
                # Метрики
                accuracy = accuracy_score(y_test, y_pred)
                try:
                    roc_auc = roc_auc_score(y_test, y_proba)
                except:
                    roc_auc = 0.5
                
                results.append({
                    'fold': i,
                    'accuracy': accuracy,
                    'roc_auc': roc_auc,
                    'n_samples': len(test_data)
                })
                
                print(f"   Accuracy: {accuracy:.3f}, ROC-AUC: {roc_auc:.3f}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                results.append({
                    'fold': i,
                    'accuracy': 0,
                    'roc_auc': 0,
                    'error': str(e)
                })
        
        # Агрегация
        if results:
            avg_accuracy = np.mean([r['accuracy'] for r in results if r['accuracy'] > 0])
            avg_roc_auc = np.mean([r['roc_auc'] for r in results if r['roc_auc'] > 0])
            std_accuracy = np.std([r['accuracy'] for r in results if r['accuracy'] > 0])
            std_roc_auc = np.std([r['roc_auc'] for r in results if r['roc_auc'] > 0])
        else:
            avg_accuracy = 0
            avg_roc_auc = 0
            std_accuracy = 0
            std_roc_auc = 0
        
        print("\n" + "=" * 80)
        print("📊 ИТОГИ WALK-FORWARD ВАЛИДАЦИИ")
        print("=" * 80)
        print(f"\n   Accuracy:  {avg_accuracy:.4f} (+/- {std_accuracy:.4f})")
        print(f"   ROC-AUC:   {avg_roc_auc:.4f} (+/- {std_roc_auc:.4f})")
        print(f"\n   Это честная оценка на НЕВИДАННЫХ данных!")
        print("=" * 80)
        
        return {
            'fold_results': results,
            'avg_accuracy': avg_accuracy,
            'avg_roc_auc': avg_roc_auc,
            'std_accuracy': std_accuracy,
            'std_roc_auc': std_roc_auc,
            'n_folds': len(folds)
        }


if __name__ == "__main__":
    print("=" * 80)
    print("INVESTEDU ML MODEL v3.0 — BACKTESTING")
    print("=" * 80)
    print("\nЭтот модуль используется для backtesting модели.")
    print("\nПример:")
    print("   from backtest_v3 import AdvancedBacktester")
    print("   backtester = AdvancedBacktester()")
    print("   results = backtester.run(model, data, feature_columns)")

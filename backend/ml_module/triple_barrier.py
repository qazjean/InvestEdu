"""
Triple Barrier Method Labeler
Из книги Маркоса Лопеса де Прадо "Advances in Financial Machine Learning"

Превращает задачу "угадывания цены через N дней" в задачу "прогнозирования исхода торговой операции"
"""

import numpy as np
import pandas as pd
from typing import List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Логирование
import logging
logger = logging.getLogger('ML_v4')


class TripleBarrierLabeler:
    """
    ✅ Класс для продвинутой разметки данных методом тройного барьера
    
    Логика:
    1. Верхний барьер (Profit Taking) → 1
    2. Нижний барьер (Stop Loss) → 0
    3. Временной барьер (Vertical) → по знаку доходности
    """
    
    def __init__(
        self,
        pt_sl_ratio: List[float] = [2.0, 1.0],
        window: int = 20,
        min_volatility: float = 0.005,
        max_volatility: float = 0.10
    ):
        """
        Args:
            pt_sl_ratio: Множители для [Profit Taking, Stop Loss]
            window: Горизонт в барах (днях)
            min_volatility: Минимальная волатильность (защита от division by zero)
            max_volatility: Максимальная волатильность (защита от аномалий)
        """
        self.pt_multiplier = pt_sl_ratio[0]
        self.sl_multiplier = pt_sl_ratio[1]
        self.window = window
        self.min_volatility = min_volatility
        self.max_volatility = max_volatility
        
        logger.info(f"   Triple Barrier: PT={self.pt_multiplier}x, SL={self.sl_multiplier}x, window={self.window} дней")
    
    def get_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        Разметка данных с учётом волатильности
        
        Args:
            df: DataFrame с данными (должен содержать 'Name', 'close')
        
        Returns:
            Series с labels (1 = profit, 0 = loss/time)
        """
        logger.info(f"Запуск Triple Barrier разметки (PT: {self.pt_multiplier}, SL: {self.sl_multiplier}, Win: {self.window})...")
        
        # 1. ✅ Считаем динамическую волатильность (стандартное отклонение LOG returns)
        # Это база для ширины барьеров
        vol = df.groupby('Name')['close'].transform(
            lambda x: np.log(x / x.shift(1)).rolling(self.window).std()
        ).fillna(method='bfill').fillna(0.01)  # fallback если данных мало

        labels = pd.Series(index=df.index, data=np.nan)

        # Обрабатываем каждый тикер отдельно, чтобы не «перепрыгивать» между акциями
        for ticker, group in df.groupby('Name'):
            prices = group['close'].values
            vols = vol.loc[group.index].values
            indices = group.index.values
            
            for i in range(len(prices) - self.window):
                start_price = prices[i]
                current_vol = vols[i]
                
                # ✅ Если волатильность нулевая, барьеры не имеют смысла
                if current_vol <= 0:
                    continue

                # ✅ Динамические границы
                up_barrier = start_price * (1 + current_vol * self.pt_multiplier)
                down_barrier = start_price * (1 - current_vol * self.sl_multiplier)
                
                # Окно будущего
                future_prices = prices[i+1 : i+1+self.window]
                
                # ✅ Находим индексы первых касаний
                touches_up = np.where(future_prices >= up_barrier)[0]
                touches_down = np.where(future_prices <= down_barrier)[0]
                
                first_up = touches_up[0] if len(touches_up) > 0 else 1e9
                first_down = touches_down[0] if len(touches_down) > 0 else 1e9
                
                if first_up < first_down and first_up < self.window:
                    labels.at[indices[i]] = 1  # ✅ Take Profit сработал раньше
                elif first_down < first_up and first_down < self.window:
                    labels.at[indices[i]] = 0  # ✅ Stop Loss сработал раньше
                else:
                    # ✅ Временной барьер: смотрим доходность на конец окна
                    labels.at[indices[i]] = 1 if future_prices[-1] > start_price else 0
        
        return labels.fillna(0).astype(int)


def apply_triple_barrier(
    df: pd.DataFrame,
    pt_ratio: float = 2.0,
    sl_ratio: float = 1.0,
    window: int = 20
) -> pd.Series:
    """
    ✅ Удобная функция для применения Triple Barrier Method
    
    Args:
        df: DataFrame с данными
        pt_ratio: Profit Taking multiplier
        sl_ratio: Stop Loss multiplier
        window: Горизонт в днях
    
    Returns:
        Series с labels
    """
    labeler = TripleBarrierLabeler(
        pt_sl_ratio=[pt_ratio, sl_ratio],
        window=window
    )
    
    return labeler.get_labels(df)


if __name__ == "__main__":
    # Тест
    logger.info("Тест Triple Barrier Method...")
    
    # Создаём тестовые данные
    np.random.seed(42)
    n = 1000
    dates = pd.date_range('2020-01-01', periods=n, freq='D')
    
    test_df = pd.DataFrame({
        'date': dates,
        'Name': 'TEST',
        'close': 100 + np.cumsum(np.random.randn(n) * 2)
    })
    
    # Применяем Triple Barrier
    labels = apply_triple_barrier(test_df, pt_ratio=2.0, sl_ratio=1.0, window=20)
    
    logger.info(f"Результат: {labels.notna().sum()} размеченных примеров")
    logger.info(f"Баланс: {labels.mean():.3f}")

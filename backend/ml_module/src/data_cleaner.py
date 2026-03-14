"""
Очистка и подготовка данных для ML-модуля

Обработка:
- Пропущенные значения (NaN)
- Выбросы
- Балансировка классов
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from typing import Tuple, Dict, Optional


class DataCleaner:
    """Очистка и подготовка данных"""
    
    def __init__(self, strategy: str = 'mean', scaling: bool = True):
        """
        Args:
            strategy: стратегия импутации ('mean', 'median', 'most_frequent', 'constant')
            scaling: нормализовать ли данные
        """
        self.strategy = strategy
        self.scaling = scaling
        self.imputer = None
        self.scaler = None
        self.feature_names = None
    
    def fit_imputer(self, X: pd.DataFrame):
        """Обучение импутера"""
        self.feature_names = X.columns.tolist()
        
        self.imputer = SimpleImputer(
            strategy=self.strategy,
            add_indicator=True  # Добавить индикатор пропущенных значений
        )
        self.imputer.fit(X)
        
        if self.scaling:
            self.scaler = StandardScaler()
            # scaler обучается после импутации
            X_imputed = self.imputer.transform(X)
            self.scaler.fit(X_imputed)
        
        return self
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Трансформация данных"""
        if self.imputer is None:
            raise ValueError("Сначала вызовите fit_imputer()")
        
        X_imputed = self.imputer.transform(X)
        
        if self.scaling:
            X_imputed = self.scaler.transform(X_imputed)
        
        return X_imputed
    
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Обучение и трансформация"""
        self.fit_imputer(X)
        return self.transform(X)
    
    def get_feature_names(self) -> list:
        """Получить имена признаков после импутации"""
        if self.imputer is None:
            raise ValueError("Импутер не обучен")
        
        # Имена оригинальных признаков
        names = list(self.feature_names)
        
        # Добавить индикаторы пропущенных значений
        if hasattr(self.imputer, 'indicator_') and self.imputer.add_indicator:
            names.extend([f"{col}_missing" for col in self.feature_names])
        
        return names


class DataBalancer:
    """Балансировка классов"""
    
    def __init__(
        self,
        method: str = 'smote',
        sampling_strategy: float = 1.0,
        random_state: int = 42
    ):
        """
        Args:
            method: 'smote', 'undersample', 'both', 'none'
            sampling_strategy: соотношение классов после балансировки
            random_state: seed для воспроизводимости
        """
        self.method = method
        self.sampling_strategy = sampling_strategy
        self.random_state = random_state
        self.balancer = None
    
    def fit_resample(
        self, 
        X: np.ndarray, 
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Балансировка данных"""
        
        if self.method == 'smote':
            self.balancer = SMOTE(
                sampling_strategy=self.sampling_strategy,
                random_state=self.random_state,
                k_neighbors=5
            )
        elif self.method == 'undersample':
            self.balancer = RandomUnderSampler(
                sampling_strategy=self.sampling_strategy,
                random_state=self.random_state
            )
        elif self.method == 'both':
            # Сначала SMOTE, потом undersampling
            smote = SMOTE(
                sampling_strategy=1.0,
                random_state=self.random_state,
                k_neighbors=5
            )
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            self.balancer = RandomUnderSampler(
                sampling_strategy=self.sampling_strategy,
                random_state=self.random_state
            )
            return self.balancer.fit_resample(X_resampled, y_resampled)
        elif self.method == 'none':
            return X, y
        else:
            raise ValueError(f"Неизвестный метод: {self.method}")
        
        return self.balancer.fit_resample(X, y)


def remove_outliers_iqr(
    df: pd.DataFrame, 
    columns: Optional[list] = None,
    threshold: float = 1.5
) -> pd.DataFrame:
    """
    Удаление выбросов методом IQR
    
    Args:
        df: DataFrame с данными
        columns: колонки для проверки (None = все числовые)
        threshold: порог IQR (1.5 = стандартный, 3.0 = более мягкий)
    
    Returns:
        DataFrame без выбросов
    """
    df = df.copy()
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    mask = np.ones(len(df), dtype=bool)
    
    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        col_mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
        mask = mask & col_mask
    
    print(f"   Удалено выбросов: {(~mask).sum()} ({(~mask).mean()*100:.2f}%)")
    
    return df[mask]


def clean_financial_data(
    df: pd.DataFrame,
    remove_outliers: bool = True,
    outlier_threshold: float = 3.0,
    impute_strategy: str = 'median'
) -> Tuple[pd.DataFrame, DataCleaner]:
    """
    Комплексная очистка финансовых данных
    
    Args:
        df: DataFrame с данными
        remove_outliers: удалять ли выбросы
        outlier_threshold: порог для выбросов
        impute_strategy: стратегия импутации NaN
    
    Returns:
        (очищенный DataFrame, объект DataCleaner)
    """
    print("=" * 70)
    print("🧹 ОЧИСТКА ФИНАНСОВЫХ ДАННЫХ")
    print("=" * 70)
    print()
    
    original_rows = len(df)
    print(f"   Исходно строк: {original_rows:,}")
    
    # 1. Удаление дубликатов
    df = df.drop_duplicates()
    dups_removed = original_rows - len(df)
    if dups_removed > 0:
        print(f"   Удалено дубликатов: {dups_removed}")
    
    # 2. Удаление выбросов
    if remove_outliers:
        print(f"   Удаление выбросов (threshold={outlier_threshold})...")
        df = remove_outliers_iqr(df, threshold=outlier_threshold)
    
    # 3. Проверка NaN
    nan_counts = df.isna().sum()
    nan_total = nan_counts.sum()
    print(f"   Пропущено значений: {nan_total:,}")
    
    if nan_total > 0:
        print(f"   Пропусков по колонкам:")
        for col, count in nan_counts.items():
            if count > 0:
                print(f"      {col}: {count:,} ({count/len(df)*100:.2f}%)")
    
    # 4. Импутация
    print(f"   Импутация (strategy={impute_strategy})...")
    cleaner = DataCleaner(strategy=impute_strategy, scaling=False)
    
    # Разделить признаки и target (если есть)
    feature_cols = [col for col in df.columns if col != 'target']
    X = df[feature_cols]
    
    X_cleaned = cleaner.fit_transform(X)
    
    # Создать DataFrame с очищенными данными
    feature_names = cleaner.get_feature_names()
    X_cleaned_df = pd.DataFrame(X_cleaned, columns=feature_names)
    
    # Добавить target обратно
    if 'target' in df.columns:
        X_cleaned_df['target'] = df['target'].values
    
    # 5. Удаление строк с NaN в target
    if 'target' in X_cleaned_df.columns:
        before = len(X_cleaned_df)
        X_cleaned_df = X_cleaned_df.dropna(subset=['target'])
        removed = before - len(X_cleaned_df)
        if removed > 0:
            print(f"   Удалено строк с NaN в target: {removed}")
    
    final_rows = len(X_cleaned_df)
    print(f"   Итого строк: {final_rows:,} ({final_rows/original_rows*100:.1f}%)")
    
    print()
    print("=" * 70)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА")
    print("=" * 70)
    print()
    
    return X_cleaned_df, cleaner


if __name__ == "__main__":
    # Тест
    print("Тест DataCleaner...")
    
    # Создать тестовые данные с NaN
    np.random.seed(42)
    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'feature3': np.random.randn(100),
        'target': np.random.randint(0, 2, 100)
    })
    
    # Добавить NaN
    df.loc[::10, 'feature1'] = np.nan
    df.loc[::15, 'feature2'] = np.nan
    
    print(f"До очистки: {len(df)} строк, {df.isna().sum().sum()} NaN")
    
    # Очистка
    df_clean, cleaner = clean_financial_data(df, remove_outliers=False)
    
    print(f"После очистки: {len(df_clean)} строк, {df_clean.isna().sum().sum()} NaN")
    print(f"Признаков: {len(df_clean.columns) - 1}")
    
    print("\n✅ Тест пройден!")

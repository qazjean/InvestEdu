"""
Этап 5: Обучение модели
Этап 6: Оценка модели

Обучение модели градиентного бустинга (XGBoost/LightGBM)
Оценка с использованием метрик: Accuracy, ROC-AUC, Precision, Recall, Confusion Matrix
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score,
    confusion_matrix, classification_report, roc_curve, precision_recall_curve
)
from sklearn.model_selection import GridSearchCV
from imblearn.over_sampling import SMOTE


class ModelTrainer:
    """Обучение модели"""

    def __init__(self, model_type: str = 'xgboost', use_optimized_params: bool = True):
        self.model_type = model_type
        self.use_optimized_params = use_optimized_params
        self.model = None
        self.metrics = {}

    def create_model(self):
        """Создание модели"""
        if self.model_type == 'xgboost':
            try:
                import xgboost as xgb
                
                if self.use_optimized_params:
                    # Оптимизированные гиперпараметры
                    self.model = xgb.XGBClassifier(
                        n_estimators=200,          # Больше деревьев
                        max_depth=8,               # Глубже деревья
                        learning_rate=0.05,        # Меньше шаг, лучше сходимость
                        subsample=0.85,            # Больше данных на дерево
                        colsample_bytree=0.85,     # Больше признаков на дерево
                        min_child_weight=3,        # Минимальный вес листа
                        gamma=0.1,                 # Регуляризация
                        reg_alpha=0.1,             # L1 регуляризация
                        reg_lambda=1.0,            # L2 регуляризация
                        random_state=42,
                        eval_metric='logloss',
                        use_label_encoder=False,
                        n_jobs=-1                  # Использовать все ядра
                    )
                    print("🤖 Модель: XGBoost (оптимизированные параметры)")
                else:
                    # Параметры по умолчанию
                    self.model = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        eval_metric='logloss',
                        use_label_encoder=False
                    )
                    print("🤖 Модель: XGBoost (параметры по умолчанию)")
                    
            except ImportError:
                print("⚠️ XGBoost не установлен, использую LightGBM")
                self.model_type = 'lightgbm'
                self.create_model()

        elif self.model_type == 'lightgbm':
            try:
                import lightgbm as lgb
                
                if self.use_optimized_params:
                    self.model = lgb.LGBMClassifier(
                        n_estimators=200,
                        max_depth=8,
                        learning_rate=0.05,
                        subsample=0.85,
                        colsample_bytree=0.85,
                        min_child_samples=20,
                        reg_alpha=0.1,
                        reg_lambda=1.0,
                        random_state=42,
                        verbose=-1,
                        n_jobs=-1
                    )
                    print("🤖 Модель: LightGBM (оптимизированные параметры)")
                else:
                    self.model = lgb.LGBMClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        verbose=-1
                    )
                    print("🤖 Модель: LightGBM (параметры по умолчанию)")
                    
            except ImportError:
                print("⚠️ LightGBM не установлен, использую RandomForest")
                from sklearn.ensemble import RandomForestClassifier
                self.model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
                self.model_type = 'randomforest'
                print("🤖 Модель: RandomForest (оптимизированные параметры)")

        return self.model
    
    def handle_imbalance(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series,
        method: str = 'smote'
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Обработка дисбаланса классов"""
        print("⚖️ Обработка дисбаланса классов...")
        
        if method == 'smote':
            try:
                smote = SMOTE(random_state=42)
                X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
                print(f"   SMOTE: {len(X_train)} → {len(X_resampled)} примеров")
                return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled)
            except Exception as e:
                print(f"   ⚠️ SMOTE ошибка: {e}, использую undersampling")
                return self._undersample(X_train, y_train)
        else:
            return self._undersample(X_train, y_train)
    
    def _undersample(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Простой undersampling"""
        df = X_train.copy()
        df['target'] = y_train
        
        class_0 = df[df['target'] == 0]
        class_1 = df[df['target'] == 1]
        
        min_samples = min(len(class_0), len(class_1))
        
        df_sampled = pd.concat([
            class_0.sample(min_samples, random_state=42),
            class_1.sample(min_samples, random_state=42)
        ])
        
        print(f"   Undersampling: {len(X_train)} → {len(df_sampled)} примеров")
        
        return df_sampled.drop('target', axis=1), df_sampled['target']
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        handle_imbalance: bool = True
    ) -> Dict:
        """Обучение модели"""
        print("=" * 70)
        print("🤖 ЭТАП 5: ОБУЧЕНИЕ МОДЕЛИ")
        print("=" * 70)
        print()
        
        # Создание модели
        self.create_model()
        print()
        
        # Обработка дисбаланса
        if handle_imbalance:
            X_train_balanced, y_train_balanced = self.handle_imbalance(X_train, y_train)
        else:
            X_train_balanced, y_train_balanced = X_train, y_train
        print()
        
        # Обучение
        print("📚 Обучение модели...")
        self.model.fit(X_train_balanced, y_train_balanced)
        print("✅ Модель обучена")
        print()
        
        # Предсказания
        print("📊 Предсказания...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        print()
        
        # Метрики
        self.metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
        
        print("=" * 70)
        print("✅ ЭТАП 5 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return self.metrics
    
    def _calculate_metrics(
        self, 
        y_true: pd.Series, 
        y_pred: np.ndarray, 
        y_pred_proba: np.ndarray
    ) -> Dict:
        """Расчёт метрик"""
        print("📊 ЭТАП 6: ОЦЕНКА МОДЕЛИ")
        print("=" * 70)
        print()
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'roc_auc': roc_auc_score(y_true, y_pred_proba),
            'precision': precision_score(y_true, y_pred),
            'recall': recall_score(y_true, y_pred),
            'f1': 2 * precision_score(y_true, y_pred) * recall_score(y_true, y_pred) / 
                  (precision_score(y_true, y_pred) + recall_score(y_true, y_pred))
        }
        
        # Confusion matrix
        metrics['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()
        
        # Печать метрик
        print("📈 Метрики модели:")
        print(f"   Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"   ROC-AUC:   {metrics['roc_auc']:.4f} ({metrics['roc_auc']*100:.2f}%)")
        print(f"   Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
        print(f"   Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
        print(f"   F1-Score:  {metrics['f1']:.4f}")
        print()
        
        print("📋 Confusion Matrix:")
        cm = metrics['confusion_matrix']
        print(f"   [[{cm[0][0]:>6}, {cm[0][1]:>6}],")
        print(f"    [{cm[1][0]:>6}, {cm[1][1]:>6}]]")
        print()
        print("   [TN, FP]")
        print("   [FN, TP]")
        print()
        
        # Classification report
        print("📝 Classification Report:")
        print(classification_report(y_true, y_pred, target_names=['Down (0)', 'Up (1)']))
        print()
        
        print("=" * 70)
        print("✅ ЭТАП 6 ЗАВЕРШЁН")
        print("=" * 70)
        print()
        
        return metrics
    
    def save_model(self, output_dir: Path):
        """Сохранение модели"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = output_dir / f'model_{self.model_type}.joblib'
        joblib.dump(self.model, model_path)
        
        metrics_path = output_dir / 'metrics.json'
        import json
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"💾 Модель сохранена в {model_path}")
        print(f"💾 Метрики сохранены в {metrics_path}")
        print()
    
    def plot_results(self, y_test: pd.Series, y_pred_proba: np.ndarray, output_dir: Path):
        """Визуализация результатов"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ROC Curve
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc_score(y_test, y_pred_proba):.3f})')
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Precision-Recall Curve
        plt.subplot(1, 2, 2)
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        plt.plot(recall, precision)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'model_curves.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"💾 Графики сохранены в {output_dir / 'model_curves.png'}")
        print()


if __name__ == "__main__":
    from data_loader import DataLoader
    from features import FeatureEngineer
    from target import TargetCreator, DataPreparator
    from pathlib import Path
    
    # Загрузка и подготовка данных
    DATA_DIR = Path(__file__).parent.parent.parent / "S&P 500 stock data"
    loader = DataLoader(DATA_DIR)
    tickers_data = loader.process_all()
    
    fe = FeatureEngineer(tickers_data)
    processed_data = fe.process_all()
    fe.remove_nan_rows()
    
    tc = TargetCreator(fe.processed_data)
    target_data = tc.process_all(days=30)
    
    dp = DataPreparator(tc.processed_data)
    X_train, X_test, y_train, y_test = dp.prepare_train_test(test_size=0.2)
    
    # Обучение модели
    trainer = ModelTrainer(model_type='xgboost')
    metrics = trainer.train(X_train, y_train, X_test, y_test, handle_imbalance=True)
    
    # Сохранение
    OUTPUT_DIR = Path(__file__).parent.parent / "models" / "trained"
    trainer.save_model(OUTPUT_DIR)
    trainer.plot_results(y_test, trainer.model.predict_proba(X_test)[:, 1], OUTPUT_DIR)

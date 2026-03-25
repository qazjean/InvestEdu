"""
ML Prediction API endpoint для frontend (v3.0 — продвинутая версия)

Поддерживает:
- Прогноз на 7 и 30 дней
- SHAP объяснения
- Калиброванные вероятности
- Детальные факторы
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import Optional

# Устанавливаем UTF-8 кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

router = APIRouter()


@router.post("/predict")
async def predict_stock(
    ticker: str = Form(...),
    csv_file: Optional[UploadFile] = File(None)
):
    """
    Прогноз роста акции v3.0

    Args:
        ticker: тикер акции (SBER, GAZP, и т.д.)
        csv_file: CSV файл с историческими данными (опционально)

    Returns:
        Прогноз с рекомендацией и объяснениями
    """
    try:
        ml_module_dir = backend_dir / 'ml_module'
        sys.path.insert(0, str(ml_module_dir))

        from predict_v3 import StockPredictorV3

        # Инициализация предиктора
        predictor = StockPredictorV3()

        if predictor.model_7d is None:
            raise HTTPException(status_code=500, detail="Модель не загружена. Сначала обучите: python ml_module/train_ultimate_v3.py")

        # Обработка CSV файла
        user_csv_path = None
        if csv_file:
            # Сохраняем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                content = await csv_file.read()
                tmp_file.write(content)
                user_csv_path = tmp_file.name

            try:
                # Прогноз с CSV
                report = predictor.predict(ticker, csv_path=user_csv_path)
            finally:
                # Удаляем временный файл
                if os.path.exists(user_csv_path):
                    os.unlink(user_csv_path)
        else:
            raise HTTPException(status_code=400, detail="CSV файл обязателен. Загрузите данные с Investing.com или Мосбиржи.")

        if 'error' in report:
            raise HTTPException(status_code=400, detail=report['error'])

        # Форматирование ответа для frontend
        return JSONResponse(content={
            'ticker': report['ticker'],
            'recommendation': report['recommendation'],
            'probability': report['probability'],
            'probability_7d': report['probability_7d'],
            'probability_30d': report['probability_30d'],
            'current_price': report['current_price'],
            'score': (report['probability'] - 0.5) * 200,
            'factors': report['factors'],
            'report_text': report['report_text'],
            'model_metrics': report.get('metrics', {})
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/info")
async def model_info():
    """
    Информация о модели v3.0
    """
    ml_module_dir = backend_dir / 'ml_module'
    sys.path.insert(0, str(ml_module_dir))

    from predict_v3 import StockPredictorV3

    predictor = StockPredictorV3()

    if predictor.model_7d is None:
        return {"status": "error", "message": "Модель не загружена"}

    return {
        "status": "ok",
        "version": "3.0",
        "model_type": "Ensemble (XGBoost + LightGBM + CatBoost)",
        "horizons": ["7 дней", "30 дней"],
        "n_features": len(predictor.feature_columns),
        "metrics_7d": {
            "accuracy": predictor.metrics.get('7d', {}).get('accuracy', 0),
            "roc_auc": predictor.metrics.get('7d', {}).get('roc_auc', 0),
            "precision": predictor.metrics.get('7d', {}).get('precision', 0),
            "recall": predictor.metrics.get('7d', {}).get('recall', 0),
            "f1": predictor.metrics.get('7d', {}).get('f1', 0)
        },
        "metrics_30d": {
            "accuracy": predictor.metrics.get('30d', {}).get('accuracy', 0),
            "roc_auc": predictor.metrics.get('30d', {}).get('roc_auc', 0),
            "precision": predictor.metrics.get('30d', {}).get('precision', 0),
            "recall": predictor.metrics.get('30d', {}).get('recall', 0),
            "f1": predictor.metrics.get('30d', {}).get('f1', 0)
        },
        "features": {
            "technical": "MA, RSI, MACD, ATR, Volatility",
            "lag": "1, 2, 3, 5, 10 дней",
            "rolling": "5, 10, 20 дней",
            "patterns": "Свечные паттерны, тренд",
            "seasonal": "День недели, месяц, квартал"
        },
        "calibration": "Isotonic (Platt scaling)",
        "explainability": "SHAP + эвристические объяснения",
        "description": "Продвинутая модель прогнозирования роста акций РФ с ансамблем, калибровкой и SHAP объяснениями"
    }


@router.get("/backtest")
async def backtest_info():
    """
    Информация о backtesting модели
    """
    return {
        "status": "ok",
        "description": "Backtesting доступен через модуль backtest_v3.py",
        "metrics": [
            "CAGR (годовая доходность)",
            "Sharpe Ratio",
            "Sortino Ratio",
            "Max Drawdown",
            "Win Rate",
            "Profit Factor",
            "Accuracy",
            "ROC-AUC"
        ],
        "conditions": {
            "commission": "0.05%",
            "slippage": "0.1%",
            "position_size": "10% от капитала"
        }
    }

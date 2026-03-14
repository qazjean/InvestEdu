"""
ML Prediction API endpoint для frontend
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
    Прогноз роста акции
    
    Args:
        ticker: тикер акции (SBER, GAZP, и т.д.)
        csv_file: CSV файл с историческими данными (опционально)
    
    Returns:
        Прогноз с рекомендацией
    """
    try:
        ml_module_dir = backend_dir / 'ml_module'
        sys.path.insert(0, str(ml_module_dir / 'src'))
        
        from prediction_api import StockPredictorAPI
        
        model_path = ml_module_dir / 'models' / 'trained' / 'model_moex_quick.joblib'
        api = StockPredictorAPI(model_path=str(model_path))
        
        if api.model is None:
            raise HTTPException(status_code=500, detail="Модель не загружена")
        
        # Обработка CSV файла
        user_csv_path = None
        if csv_file:
            # Сохраняем временный файл
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                content = await csv_file.read()
                tmp_file.write(content)
                user_csv_path = tmp_file.name
            
            try:
                # Прогноз с CSV
                report = api.predict(ticker, user_csv_path=user_csv_path)
            finally:
                # Удаляем временный файл
                if os.path.exists(user_csv_path):
                    os.unlink(user_csv_path)
        else:
            # Прогноз без CSV (используем Yahoo Finance)
            report = api.predict(ticker, use_yfinance=True)
        
        if 'error' in report:
            raise HTTPException(status_code=400, detail=report['error'])
        
        return JSONResponse(content=report)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/info")
async def model_info():
    """
    Информация о модели
    """
    ml_module_dir = backend_dir / 'ml_module'
    sys.path.insert(0, str(ml_module_dir / 'src'))
    
    from prediction_api import StockPredictorAPI
    
    model_path = ml_module_dir / 'models' / 'trained' / 'model_moex_quick.joblib'
    api = StockPredictorAPI(model_path=str(model_path))
    
    if api.model is None:
        return {"status": "error", "message": "Модель не загружена"}
    
    return {
        "status": "ok",
        "accuracy": api.metrics.get('accuracy', 0),
        "roc_auc": api.metrics.get('roc_auc', 0),
        "precision": api.metrics.get('precision', 0),
        "recall": api.metrics.get('recall', 0),
        "f1": api.metrics.get('f1', 0),
        "n_features": len(api.feature_columns),
        "description": "Модель прогнозирования роста акций РФ (MOEX + ЦБ РФ)"
    }

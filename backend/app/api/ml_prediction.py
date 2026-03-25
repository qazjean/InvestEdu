"""
ML Prediction API endpoint для frontend
Использует модель v4.0 (XGBoost Multiclass + Triple Barrier)
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

# ✅ Путь к последней модели v4
ML_MODULE_DIR = backend_dir / 'ml_module'
MODEL_DIR = ML_MODULE_DIR / 'models' / 'trained'


def get_latest_v4_model_path() -> Path:
    """Поиск последней РАБОЧЕЙ модели v4"""
    # model_real_final.joblib — сохранена правильно, работает без костылей
    real_final = MODEL_DIR / 'model_real_final.joblib'
    if real_final.exists() and real_final.stat().st_size > 1_000_000:
        return real_final
    
    # Fallback на ultimate v4 (может не работать из-за путей импорта)
    return MODEL_DIR / 'model_ultimate_v4_20260322_120034.joblib'


@router.post("/predict")
async def predict_stock(
    ticker: str = Form(...),
    csv_file: Optional[UploadFile] = File(None)
):
    """
    Прогноз роста акции используя модель v4.0

    Args:
        ticker: тикер акции (SBER, GAZP, и т.д.)
        csv_file: CSV файл с историческими данными (опционально)

    Returns:
        Прогноз с рекомендацией
    """
    try:
        # ✅ Добавляем ml_module и src в path
        sys.path.insert(0, str(ML_MODULE_DIR))
        sys.path.insert(0, str(ML_MODULE_DIR / 'src'))

        # ✅ Используем модель v4
        from predict_v4 import StockPredictorV4

        model_path = get_latest_v4_model_path()
        print(f"📥 Используем модель: {model_path.name} ({model_path.stat().st_size / 1_000_000:.1f} MB)")

        predictor = StockPredictorV4(model_path=str(model_path))

        if predictor.models is None:
            raise HTTPException(status_code=500, detail="Модель не загружена")

        # Обработка CSV файла
        user_csv_path = None
        if csv_file:
            try:
                import tempfile
                import os
                import io

                # Читаем контент
                content = await csv_file.read()
                print(f"\n📥 ЗАГРУЗКА ФАЙЛА: {csv_file.filename}")
                print(f"   Размер: {len(content)} байт")

                # Декодируем если bytes
                if isinstance(content, bytes):
                    for enc in ['utf-8', 'cp1251', 'latin1', 'utf-8-sig']:
                        try:
                            content = content.decode(enc)
                            print(f"   ✅ Кодировка: {enc}")
                            break
                        except:
                            continue
                    else:
                        content = content.decode('utf-8', errors='ignore')

                # 🔍 Показываем первые 300 символов
                print(f"   📋 Начало: {repr(content[:300])}")

                # 🔥 УБИРАЕМ ЛИШНИЕ КАВЫЧКИ (браузер экранирует "" вместо ")
                # Сначала заменяем "" на ", потом убираем кавычки в начале/конце строк
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Убираем кавычки в начале и конце строки
                    line = line.strip()
                    if line.startswith('"') and line.endswith('"'):
                        line = line[1:-1]
                    # Заменяем "" на " внутри строки
                    line = line.replace('""', '"')
                    cleaned_lines.append(line)
                content = '\n'.join(cleaned_lines)
                print(f"   ✅ Убраны лишние кавычки")
                print(f"   📋 После очистки: {repr(content[:200])}")

                # 🔍 СОХРАНЯЕМ для отладки
                with open('debug_raw_file.csv', 'w', encoding='utf-8') as f:
                    f.write(content)

                # ✅ ПАРСИМ ЧЕРЕЗ PANDAS ПРЯМО ИЗ ПАМЯТИ
                import pandas as pd
                for enc in ['utf-8', 'cp1251', 'latin1']:
                    try:
                        df = pd.read_csv(
                            io.StringIO(content),
                            encoding=enc,
                            quotechar='"',
                            skipinitialspace=True
                        )
                        print(f"   ✅ Pandas прочитал: {len(df)} строк")
                        print(f"   ✅ Колонки: {list(df.columns)}")
                        break
                    except Exception as e:
                        print(f"   ⚠️ {enc}: {e}")
                        continue
                else:
                    return {'error': f'Не удалось прочитать CSV'}

                # Сохраняем как временный файл для predict_v4
                file_suffix = Path(csv_file.filename).suffix if csv_file.filename else '.csv'
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix, mode='w', encoding='utf-8', newline='') as tmp_file:
                    tmp_file.write(content)
                    user_csv_path = tmp_file.name

                print(f"   ✅ Временный файл: {user_csv_path}")

                # Прогноз с CSV
                report = predictor.predict(ticker, csv_path=user_csv_path)
            finally:
                # Удаляем временный файл
                if user_csv_path and os.path.exists(user_csv_path):
                    try:
                        os.unlink(user_csv_path)
                        print(f"✅ Временный файл удалён: {user_csv_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось удалить файл: {e}")
        else:
            # Прогноз без CSV (используем Yahoo Finance)
            report = predictor.predict(ticker, csv_path=None)

        if 'error' in report:
            raise HTTPException(status_code=400, detail=report['error'])

        return JSONResponse(content=report)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/info")
async def model_info():
    """
    Информация о модели v4
    """
    import json
    
    # Модель от 22 марта
    model_file = "model_ultimate_v4_20260322_120034.joblib"
    metrics_file = "metrics_ultimate_v4_20260322_120035.json"
    
    metrics = {}
    try:
        with open(MODEL_DIR / metrics_file, 'r') as f:
            metrics = json.load(f)
    except:
        pass
    
    return {
        "status": "ok",
        "model_version": "v4.0 (Multiclass Triple Barrier)",
        "model_file": model_file,
        "horizons": ["7", "30"],
        "metrics": metrics,
        "n_features": 148,
        "description": "Модель прогнозирования роста акций РФ (MOEX + ЦБ РФ) с Triple Barrier Method"
    }


# Популярные российские акции для отображения (без прогнозов, только цены)
POPULAR_RU_STOCKS = [
    {"ticker": "SBER", "name": "Сбербанк", "yf_ticker": "SBER.ME"},
    {"ticker": "GAZP", "name": "Газпром", "yf_ticker": "GAZP.ME"},
    {"ticker": "LKOH", "name": "Лукойл", "yf_ticker": "LKOH.ME"},
    {"ticker": "YNDX", "name": "Яндекс", "yf_ticker": "YNDX.ME"},
    {"ticker": "TCSG", "name": "Тинькофф", "yf_ticker": "TCSG.ME"},
    {"ticker": "VTBR", "name": "ВТБ", "yf_ticker": "VTBR.ME"},
    {"ticker": "ROSN", "name": "Роснефть", "yf_ticker": "ROSN.ME"},
    {"ticker": "GMKN", "name": "Норникель", "yf_ticker": "GMKN.ME"},
    {"ticker": "NVTK", "name": "Новатэк", "yf_ticker": "NVTK.ME"},
    {"ticker": "SNGS", "name": "Сургутнефтегаз", "yf_ticker": "SNGS.ME"},
    {"ticker": "PHOR", "name": "ФосАгро", "yf_ticker": "PHOR.ME"},
    {"ticker": "MTSS", "name": "МТС", "yf_ticker": "MTSS.ME"},
]

# Кэш цен (обновляется автоматически при запросе)
_stock_prices_cache = {
    "data": [],
    "timestamp": None
}

@router.get("/top-stocks")
async def get_top_stocks(limit: int = 12):
    """Популярные российские акции с актуальными ценами"""
    from datetime import datetime
    from pathlib import Path
    import json
    
    now = datetime.now()
    
    # Обновляем кэш если старый (> 1 часа) или пустой
    need_refresh = (
        not _stock_prices_cache["data"] or 
        (_stock_prices_cache["timestamp"] and 
         (now - _stock_prices_cache["timestamp"]).seconds > 3600)
    )
    
    if need_refresh:
        print("Загрузка цен из файла...")
        
        # Путь к файлу с ценами
        data_dir = Path(__file__).parent.parent / "data"
        prices_file = data_dir / "stock_prices.json"
        
        try:
            if prices_file.exists():
                with open(prices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _stock_prices_cache["data"] = data.get("top_stocks", [])[:limit]
                    print(f"Загружено {len(_stock_prices_cache['data'])} акций из файла")
            else:
                print("Файл stock_prices.json не найден")
                _stock_prices_cache["data"] = []
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
            _stock_prices_cache["data"] = []
        
        _stock_prices_cache["timestamp"] = now
    
    return {
        "top_stocks": _stock_prices_cache["data"],
        "updated_at": _stock_prices_cache["timestamp"].strftime("%Y-%m-%d %H:%M") if _stock_prices_cache["timestamp"] else "N/A",
        "source": "Московская Биржа",
        "cache_age_minutes": round((now - _stock_prices_cache["timestamp"]).seconds / 60, 1) if _stock_prices_cache["timestamp"] else 999
    }

@router.post("/top-stocks/refresh")
async def refresh_top_stocks():
    """Принудительное обновление кэша цен"""
    from datetime import datetime
    
    # Сбрасываем кэш
    _stock_prices_cache["data"] = []
    _stock_prices_cache["timestamp"] = None
    
    # Вызываем get_top_stocks для обновления
    return await get_top_stocks()


@router.get("/macro")
async def get_macro_data():
    """
    Актуальные макроданные: ключевая ставка, курсы валют, нефть
    Источник: ЦБ РФ + открытые данные
    """
    import httpx
    from datetime import datetime
    
    # Данные по умолчанию (актуальные на март 2026)
    macro = {
        "key_rate": 15.0,      # Ключевая ставка ЦБ
        "usd_rub": 80.53,       # USD/RUB
        "eur_rub": 93.30,       # EUR/RUB
        "oil_price": 104.2,     # Нефть Brent $
        "inflation": 5.91,      # Инфляция %
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "ЦБ РФ (оценочные данные)"
    }
    
    # Попытка загрузить актуальные данные
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # ЦБ РФ
            resp = await client.get("https://www.cbr-xml-daily.ru/json")
            if resp.status_code == 200:
                data = resp.json()
                if 'key_rate' in data:
                    macro["key_rate"] = data['key_rate']
                if 'Valute' in data:
                    macro["usd_rub"] = data['Valute'].get('USD', {}).get('Value', 90.0)
                    macro["eur_rub"] = data['Valute'].get('EUR', {}).get('Value', 98.0)
    except Exception as e:
        print(f"⚠Не удалось загрузить данные ЦБ: {e}")
    
    # Нефть Brent (ориентировочно)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.brentcrudeprice.com/price")
            if resp.status_code == 200:
                data = resp.json()
                macro["oil_price"] = float(data.get('price', 85.0))
    except:
        pass
    
    return macro

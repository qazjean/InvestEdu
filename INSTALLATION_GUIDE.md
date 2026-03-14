# InvestEdu — Инструкция по установке и запуску

Подробное руководство по развёртыванию платформы для обучения инвестициям.

---

## Содержание

1. [Требования к системе](#требования-к-системе)
2. [Установка Backend](#установка-backend)
3. [Установка Frontend](#установка-frontend)
4. [Инициализация базы данных](#инициализация-базы-данных)
5. [Запуск приложения](#запуск-приложения)
6. [Проверка работоспособности](#проверка-работоспособности)
7. [Настройка ML-модуля](#настройка-ml-модуля)
8. [Обучение ML-модели](#обучение-ml-модели)
9. [Использование AI-прогнозов](#использование-ai-прогнозов)
10. [Частые проблемы и решения](#частые-проблемы-и-решения)

---

## Требования к системе

### Минимальные требования

- **Операционная система:** Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Процессор:** 2 ядра, 2.0 GHz
- **Оперативная память:** 4 GB
- **Свободное место:** 5 GB

### Рекомендуемые требования

- **Операционная система:** Windows 11, macOS 12+, Linux (Ubuntu 22.04+)
- **Процессор:** 4 ядра, 2.5 GHz+
- **Оперативная память:** 8 GB
- **Свободное место:** 10 GB (с учётом датасетов)

### Необходимое ПО

- **Python:** версии 3.10 или выше
- **Node.js:** версии 18.x или выше
- **npm:** версии 9.x или выше
- **Git:** для клонирования репозитория

---
## ПРОЩЕ ВСЕГО УСТАНОВИТЬ ПРИЛОЖЕНИЕ ПУТЕМ РАЗАХИВИРОВАНИЯ ZIP АРХИВА. На GitHub нельзя загрузить тяжелые данные, поэтому настраивать приложение нужно будет заново.
## Установка Backend

### Шаг 1: Перейдите в директорию backend

```bash
cd backend
```

### Шаг 2: Создайте виртуальное окружение

**Для Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Для macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 3: Установите зависимости

```bash
pip install -r requirements.txt
```

### Шаг 4: Проверьте установку

```bash
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
```

Ожидаемый вывод: `FastAPI version: 0.109.0` или выше.

---

## Установка Frontend

### Шаг 1: Перейдите в директорию frontend

```bash
cd frontend
```

### Шаг 2: Установите зависимости

```bash
npm install
```

Процесс установки может занять 2-5 минут в зависимости от скорости интернета.

### Шаг 3: Проверьте установку

```bash
npm list react react-dom
```

Ожидаемый вывод: версии React 18.2.0 или выше.

---

## Инициализация базы данных

### Шаг 1: Перейдите в директорию backend

```bash
cd backend
```

### Шаг 2: Проверьте содержимое БД. Если оно пусто, то Запустите инициализацию БД

```bash
python -m app.services.init_db
```

### Шаг 3: Проверьте результат

Вы должны увидеть:

```
Импортировано 5 модулей
Импортировано 40 уроков
Импортировано 6 кейсов

База данных успешно инициализирована!
```

### Шаг 4: Проверьте файл БД

Убедитесь, что файл создан:

```bash
# Windows
dir app\data\invest_edu.db

# macOS/Linux
ls -lh app/data/invest_edu.db
```

Размер файла должен быть примерно 500 KB - 1 MB.

---

## Запуск приложения

### Запуск Backend

**Вариант 1: Обычный запуск**

```bash
cd backend
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # macOS/Linux

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Вариант 2: В фоновом режиме (Windows)**

```bash
start python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Вариант 3: В фоновом режиме (macOS/Linux)**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```

### Запуск Frontend

Откройте новый терминал:

```bash
cd frontend
npm run dev
```

Ожидаемый вывод:

```
VITE v5.0.11  ready in 500 ms

Local:   http://localhost:5173/
Network: use --host to expose
```

---

## Проверка работоспособности

### Проверка Backend

1. Откройте браузер
2. Перейдите по адресу: `http://localhost:8000`
3. Вы должны увидеть: `{"message": "InvestEdu API запущен", "version": "1.0.0"}`

### Проверка Swagger UI

1. Перейдите по адресу: `http://localhost:8000/docs`
2. Вы должны увидеть интерактивную документацию API со всеми эндпоинтами

### Проверка Frontend

1. Откройте браузер
2. Перейдите по адресу: `http://localhost:5173`
3. Вы должны увидеть главную страницу приложения с тремя разделами:
   - Глубокая теория
   - Реальные кейсы
   - AI Assistant

### Проверка API эндпоинтов

**Получить список модулей:**

```bash
curl http://localhost:8000/api/courses/modules
```

**Получить список кейсов:**

```bash
curl http://localhost:8000/api/cases/
```

**Получить информацию о ML модели:**

```bash
curl http://localhost:8000/api/ml/info
```

---

## Настройка ML-модуля

### Шаг 1: Перейдите в директорию ml_module

```bash
cd backend/ml_module
```

### Шаг 2: Установите дополнительные зависимости

```bash
pip install -r requirements.txt
```

### Шаг 3: Проверьте наличие обученной модели

```bash
# Windows
dir models\trained\model_real_final.joblib

# macOS/Linux
ls -lh models/trained/model_real_final.joblib
```

Если файл существует (размер примерно 5-15 MB), модель уже обучена и готова к использованию.

### Шаг 4: Если модель отсутствует

Перейдите к разделу [Обучение ML-модели](#обучение-ml-модели).

---

## Обучение ML-модели

### Вариант 1: Быстрое обучение (рекомендуется для тестирования)

**Время обучения:** 5-10 минут

**Требования:**
- Интернет-соединение (для загрузки данных Yahoo Finance)
- 2 GB свободного места

**Команда:**

```bash
cd backend
python train_quick_stable.py
```

**Результат:**
- Модель: `ml_module/models/trained/model_moex_quick.joblib`
- Метрики: `ml_module/models/trained/metrics_moex_quick.json`

### Вариант 2: Полное обучение (рекомендуется для продакшена)

**Время обучения:** 15-30 минут

**Требования:**
- Интернет-соединение
- 5 GB свободного места
- Данные ЦБ РФ, датасетов (есть в архиве на гугл диске)

**Шаг 1: Загрузите данные ЦБ РФ**

```bash
cd backend
python load_cb_data_fixed.py
```

**Шаг 2: Запустите обучение**

```bash
python train_real_final_v2.py
```

**Результат:**
- Модель: `ml_module/models/trained/model_real_final.joblib`
- Метрики: `ml_module/models/trained/metrics_real_final.json`

### Шаг 3: Проверьте метрики

После обучения вы увидите:

```
Accuracy: 0.58-0.65
ROC-AUC: 0.60-0.68
Precision: 0.58-0.65
Recall: 0.58-0.65
F1-Score: 0.58-0.65
```

---

## Использование AI-прогнозов

### Через веб-интерфейс

1. Откройте `http://localhost:5173/ai-assistant`
2. Введите тикер акции (например: SBER, GAZP, LKOH), прикрепите .csv с динакомикой роста акций. Большинство сервисов не позволяют повторно размещать свои данные, но на сате указано, где можно скачать датасет
3. Нажмите "Получить прогноз"
4. Получите рекомендацию с вероятностью роста


## Возможные проблемы и решения

### Проблема 1: Backend не запускается

**Ошибка:** `ModuleNotFoundError: No module named 'fastapi'`

**Решение:**

```bash
cd backend
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Проблема 2: Frontend не запускается

**Ошибка:** `npm: command not found`

**Решение:**

1. Установите Node.js с официального сайта: https://nodejs.org/
2. Проверьте установку: `node --version`
3. Попробуйте снова: `npm install`

### Проблема 3: Ошибка при инициализации БД

**Ошибка:** `sqlite3.OperationalError: no such table: modules`

**Решение:**

```bash
cd backend
python -m app.services.init_db --force
```

### Проблема 4: Модель не загружается

**Ошибка:** `Model not found: ml_module/models/trained/model_real_final.joblib`

**Решение:**

1. Проверьте наличие файла:
   ```bash
   dir ml_module\models\trained\
   ```

2. Если файл отсутствует, обучите модель:
   ```bash
   python train_quick_stable.py
   ```

### Проблема 5: CORS ошибка при запросах

**Ошибка:** `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**Решение:**

Убедитесь, что в `backend/app/main.py` настроен CORS:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проблема 6: Данные не загружаются из Yahoo Finance

**Ошибка:** `Failed to download data`

**Решение:**

1. Проверьте интернет-соединение
2. Yahoo Finance может временно блокировать запросы
3. Попробуйте позже или используйте локальные данные:
   ```bash
   python load_cb_data_fixed.py
   ```

### Проблема 7: Port 8000 уже занят

**Ошибка:** `Address already in use: port 8000`

**Решение:**

**Windows:**

```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**macOS/Linux:**

```bash
lsof -i :8000
kill -9 <PID>
```

Или используйте другой порт:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Проблема 8: Port 5173 уже занят

**Ошибка:** `Port 5173 is already in use`

**Решение:**

```bash
npm run dev -- --port 5174
```

Затем откройте `http://localhost:5174`

---

## Дополнительные команды

### Управление базой данных

**Просмотр статистики БД:**

```bash
cd backend
python -m app.services.manage_db stats
```

**Создание бэкапа БД:**

```bash
python -m app.services.manage_db backup
```

**Экспорт данных в JSON:**

```bash
python -m app.services.manage_db export
```

### Проверка API

**Тестовый запрос:**

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ: `{"status": "healthy"}`

### Остановка приложения

**Backend:**

Нажмите `Ctrl+C` в терминале где запущен uvicorn.

**Frontend:**

Нажмите `Ctrl+C` в терминале где запущен Vite.

---

## Структура проекта после установки

```
pythonproject281/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── courses.py
│   │   │   ├── cases.py
│   │   │   ├── market_data.py
│   │   │   └── ml_prediction.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── init_db.py
│   │   │   ├── manage_db.py
│   │   │   └── generate_cases.py
│   │   ├── data/
│   │   │   ├── invest_edu.db
│   │   │   ├── lessons_data.json
│   │   │   └── curriculum.md
│   │   └── main.py
│   ├── ml_module/
│   │   ├── src/
│   │   │   ├── features.py
│   │   │   ├── target.py
│   │   │   ├── train.py
│   │   │   └── predict.py
│   │   ├── models/
│   │   │   └── trained/
│   │   │       ├── model_real_final.joblib
│   │   │       └── metrics_real_final.json
│   │   └── data/
│   │       └── macro/
│   │           ├── usd_rub.csv
│   │           └── inflation_rate.csv
│   ├── venv/
│   ├── requirements.txt
│   └── train_real_final_v2.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── CoursesPage.tsx
│   │   │   ├── LessonViewPage.tsx
│   │   │   ├── CasesPage.tsx
│   │   │   ├── CaseDetailPage.tsx
│   │   │   ├── AIAssistantPage.tsx
│   │   │   └── GlossaryPage.tsx
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   └── Footer.tsx
│   │   └── App.tsx
│   ├── node_modules/
│   ├── package.json
│   └── vite.config.ts
└── READMEs.md
```


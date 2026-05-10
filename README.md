# 🤖 AI-генератор постов для Telegram

Автоматизированный сервис для сбора новостей, генерации привлекательных постов с помощью AI и публикации в Telegram-канал.

## 📋 Содержание

- [✨ Возможности](#-возможности)
- [🛠 Технологии](#-технологии)
- [📦 Установка](#-установка)
- [⚙️ Настройка](#️-настройка)
- [🚀 Запуск](#-запуск)
- [📚 API Эндпоинты](#-api-эндпоинты)
- [🔍 Примеры запросов](#-примеры-запросов)
- [🌐 Парсинг Lenta.ru](#-парсинг-lentaru)
- [📁 Структура проекта](#-структура-проекта)
- [🔧 Устранение проблем](#-устранение-проблем)
- [🧪 Проверка работоспособности](#-проверка-работоспособности)
- [📊 Мониторинг](#-мониторинг)
- [🐛 Известные ограничения](#-известные-ограничения)

## ✨ Возможности

- 🔄 **Автоматический сбор новостей** из Lenta.ru (RSS)
- 🤖 **AI-генерация постов** (с поддержкой OpenAI GPT)
- 📅 **Публикация по расписанию** с помощью Celery Beat
- 🎯 **Фильтрация контента** по ключевым словам
- 📊 **REST API** для управления источниками и мониторинга
- 📝 **Swagger документация** API
- 🐳 **Docker поддержка** для Redis
- 💾 **SQLite база данных** (легкая для разработки)

## 🛠 Технологии

- **FastAPI** - веб-фреймворк
- **Celery** - очередь задач
- **Redis** - брокер сообщений
- **SQLAlchemy** - ORM
- **SQLite** - база данных (может быть заменена на PostgreSQL)
- **BeautifulSoup4** - парсинг сайтов
- **FeedParser** - парсинг RSS
- **Uvicorn** - ASGI сервер

## 📦 Установка
### 1. Клонирование репозитория
git clone <your-repository-url>
cd NewsAggregator
### 2. Создание виртуального окружения
powershell
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
3. Установка зависимостей
pip install -r requirements.txt
4. Настройка переменных окружения
Создайте файл .env в корне проекта
5. 
# База данных
DATABASE_URL=sqlite:///./aibot.db

# Redis для Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# OpenAI (опционально, для тестов можно оставить заглушку)
OPENAI_API_KEY=test_key
OPENAI_MODEL=gpt-4

# Telegram (заглушки для тестов)
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=test_hash
TELEGRAM_BOT_TOKEN=test_token
TELEGRAM_CHANNEL_ID=@test_channel

# Режим отладки
DEBUG=True
🚀 Запуск
Быстрый запуск (только API)
uvicorn app.main:app --reload
После запуска откройте в браузере:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
API Root: http://localhost:8000/

Полный запуск (API + Celery + Redis)
1. Запустите Redis (через Docker)
# Запуск Redis контейнера
docker run -d -p 6379:6379 --name redis redis

# Проверка, что Redis работает
docker ps

# Просмотр логов Redis
docker logs redis

# Остановка Redis
docker stop redis

# Запуск остановленного Redis
docker start redis

# Удаление контейнера Redis
docker rm redis

2. Запустите FastAPI сервер (Terminal 1)
uvicorn app.main:app --reload
3. Запустите Celery worker (Terminal 2)
celery -A app.tasks worker --loglevel=info --pool=solo
4. Запустите Celery beat (Terminal 3)
celery -A app.tasks beat --loglevel=info
Запуск всех сервисов одной командой (Windows PowerShell)
Создайте файл start_all.ps1:
# start_all.ps1
Write-Host "Starting all services..." -ForegroundColor Green

# Запускаем Redis если не запущен
$redisRunning = docker ps | findstr redis
if (-not $redisRunning) {
    Write-Host "Starting Redis..." -ForegroundColor Yellow
    docker start redis 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker run -d -p 6379:6379 --name redis redis
    }
}

# Запускаем FastAPI
Write-Host "Starting FastAPI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; uvicorn app.main:app --reload --port 8000"

# Запускаем Celery worker
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; celery -A app.tasks worker --loglevel=info --pool=solo"

# Запускаем Celery beat
Write-Host "Starting Celery beat..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; celery -A app.tasks beat --loglevel=info"

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "📚 Swagger UI: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🐳 Redis: localhost:6379" -ForegroundColor Cyan
Запустите:
.\start_all.ps1

📚 API Эндпоинты
Управление источниками
Метод	Эндпоинт	Описание
GET	/api/sources/	Получить все источники
POST	/api/sources/	Создать источник
PUT	/api/sources/{id}	Обновить источник
DELETE	/api/sources/{id}	Удалить источник
POST	/api/sources/{id}/parse	Запустить парсинг источника
Управление ключевыми словами
Метод	Эндпоинт	Описание
GET	/api/keywords/	Получить все ключевые слова
POST	/api/keywords/	Добавить ключевое слово
DELETE	/api/keywords/{id}	Удалить ключевое слово
PUT	/api/keywords/{id}/toggle	Вкл/Выкл ключевое слово
POST	/api/keywords/bulk-add	Добавить несколько слов
Новости
Метод	Эндпоинт	Описание
GET	/api/news/	Получить список новостей
GET	/api/news/{id}	Получить новость по ID
GET	/api/news/latest	Последние новости
GET	/api/news/by-keyword/{keyword}	Поиск по ключевому слову
POST	/api/news/{id}/generate	Сгенерировать пост
Посты
Метод	Эндпоинт	Описание
GET	/api/posts/	Получить список постов
GET	/api/posts/{id}	Получить пост по ID
POST	/api/posts/{id}/publish	Опубликовать пост
DELETE	/api/posts/{id}	Удалить пост
Парсинг
Метод	Эндпоинт	Описание
POST	/api/parse/lenta	Запустить парсинг Lenta.ru
Прочее
Метод	Эндпоинт	Описание
POST	/api/generate/	Ручная генерация поста
GET	/api/stats/	Статистика системы
GET	/api/health	Проверка здоровья
GET	/api/dashboard	Дашборд

🔍 Примеры запросов
Добавление ключевых слов
# Через curl
curl -X POST "http://localhost:8000/api/keywords/" -H "Content-Type: application/json" -d "{\"word\": \"Россия\"}"
curl -X POST "http://localhost:8000/api/keywords/" -H "Content-Type: application/json" -d "{\"word\": \"технологии\"}"
curl -X POST "http://localhost:8000/api/keywords/" -H "Content-Type: application/json" -d "{\"word\": \"искусственный интеллект\"}"

# Добавить несколько сразу
curl -X POST "http://localhost:8000/api/keywords/bulk-add" -H "Content-Type: application/json" -d "[\"Россия\", \"технологии\", \"IT\", \"нейросети\"]"
Парсинг Lenta.ru
bash
# Запустить парсинг
curl -X POST "http://localhost:8000/api/parse/lenta"

# Ожидаемый ответ:
# {
#   "status": "success",
#   "total_parsed": 30,
#   "filtered": 5,
#   "new_news": 3
# }
Просмотр данных
# Статистика системы
curl "http://localhost:8000/api/stats/"

# Все новости
curl "http://localhost:8000/api/news/"

# Последние 10 новостей
curl "http://localhost:8000/api/news/latest?limit=10"

# Поиск по ключевому слову
curl "http://localhost:8000/api/news/by-keyword/Россия"

# Все посты
curl "http://localhost:8000/api/posts/"

# Дашборд
curl "http://localhost:8000/api/dashboard"

# Проверка здоровья
curl "http://localhost:8000/api/health"

Генерация поста
# Ручная генерация
curl -X POST "http://localhost:8000/api/generate/" -H "Content-Type: application/json" -d "{\"title\": \"Новая технология AI\", \"summary\": \"Ученые разработали новую нейросеть, которая способна генерировать видео по текстовому описанию\"}"
Управление источниками
# Создать источник
curl -X POST "http://localhost:8000/api/sources/" -H "Content-Type: application/json" -d "{\"type\": \"site\", \"name\": \"Lenta.ru\", \"url\": \"https://lenta.ru\", \"enabled\": true}"

# Получить все источники
curl "http://localhost:8000/api/sources/"
🌐 Парсинг Lenta.ru
Парсинг RSS: Система парсит RSS-ленту Lenta.ru (https://lenta.ru/rss)
Фильтрация: Новости фильтруются по ключевым словам из базы данных
Сохранение: Релевантные новости сохраняются в базу данных
Генерация: Для каждой новости автоматически генерируется пост

# Автоматический парсинг
С Celery Beat парсинг запускается автоматически:
⏰ Каждые 30 минут - парсинг Lenta.ru
⏰ Каждые 10 минут - генерация постов для новых новостей
⏰ Каждый день в полночь - очистка старых логов

# Ручной парсинг
# Через API
curl -X POST "http://localhost:8000/api/parse/lenta"

# Или через Python
python -c "from app.tasks import parse_lenta_by_keywords; print(parse_lenta_by_keywords.delay().get())"
Тестирование парсинга
Создайте файл test_parse.py:
"""Тестовый скрипт для парсинга Lenta.ru"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.news_parser.lenta_parser import LentaParser
from app.database import db
from app.models import NewsItem, Keyword

def test_parse():
    print("🚀 Starting Lenta.ru parser test...")
    
    parser = LentaParser()
    news_items = parser.parse_rss()
    print(f"✅ Parsed {len(news_items)} news")
    
    print("\n📰 Latest news:")
    for i, news in enumerate(news_items[:5], 1):
        print(f"{i}. {news['title']}")
        print(f"   URL: {news['url']}")
        print()
    
    session = db.get_session()
    keywords = session.query(Keyword).filter(Keyword.is_active == True).all()
    keyword_list = [kw.word for kw in keywords]
    print(f"🔑 Active keywords: {', '.join(keyword_list)}")
    session.close()

if __name__ == "__main__":
    test_parse()

Запуск:
python test_parse.py

📁 Структура проекта
NewsAggregator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   ├── config.py               # Конфигурация
│   ├── database.py             # Подключение к БД
│   ├── models.py               # SQLAlchemy модели
│   ├── tasks.py                # Celery задачи
│   ├── api/
│   │   ├── __init__.py
│   │   └── simple_endpoints.py # API эндпоинты
│   ├── news_parser/
│   │   ├── __init__.py
│   │   └── lenta_parser.py     # Парсер Lenta.ru
│   └── ai/
│       ├── __init__.py
│       ├── generator.py        # AI генерация
│       └── openai_client.py    # OpenAI клиент
├── celery_worker.py            # Точка входа Celery
├── requirements.txt            # Зависимости
├── .env                        # Переменные окружения
├── .env.example                # Пример .env файла
├── .gitignore                  # Git ignore файл
├── start_all.ps1               # Скрипт запуска (Windows)
├── test_parse.py               # Тестовый скрипт
└── README.md                   # Документация

🔧 Устранение проблем
Ошибка: NameError: name 'router' is not defined
Решение: Убедитесь, что в файле app/api/simple_endpoints.py есть строка:

router = APIRouter(prefix="/api", tags=["API"])
Ошибка: ValueError: invalid literal for int()
Решение: Проверьте файл .env, убедитесь что TELEGRAM_API_ID содержит число:

# env:
TELEGRAM_API_ID=12345
Ошибка: sqlalchemy.exc.CompileError с UUID
Решение: Используйте SQLite с String(36) вместо UUID или переключитесь на PostgreSQL.

## Redis не запускается
# Проверьте статус Docker
docker ps
# Если Docker не запущен - запустите Docker Desktop

# Перезапустите Redis
docker stop redis
docker rm redis
docker run -d -p 6379:6379 --name redis redis
Celery не подключается к Redis
# Проверьте подключение
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
# Должно вернуть True
Порт 8000 уже занят
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# Linux/Mac
lsof -i :8000
kill -9 <PID>

## Файл .env должен содержать:
DATABASE_URL=sqlite:///./aibot.db
DEBUG=True
Приложение автоматически создаст таблицы при первом запуске.

🧪 Проверка работоспособности
1. Проверка API
curl http://localhost:8000/
# Ожидаемый ответ: {"message":"Welcome to AI News Bot","docs":"/docs","status":"running"}
2. Проверка здоровья
curl http://localhost:8000/api/health
# Ожидаемый ответ: {"status":"ok","database":"healthy","api_version":"1.0.0"}
3. Проверка Celery (если запущен)
python -c "from app.tasks import test_celery; print(test_celery.delay().get(timeout=10))"
4. Проверка парсинга
# Добавить тестовое ключевое слово
curl -X POST "http://localhost:8000/api/keywords/" -H "Content-Type: application/json" -d "{\"word\": \"новости\"}"

# Запустить парсинг
curl -X POST "http://localhost:8000/api/parse/lenta"

# Проверить результат
curl "http://localhost:8000/api/stats/"

📊 Мониторинг
# Просмотр логов
Логи FastAPI (в терминале с uvicorn)
Логи Celery (в терминалах worker и beat)
Логи Redis
docker logs redis

# Просмотр данных в БД
Установите SQLite Browser
Или через командную строку:
sqlite3 aibot.db
.tables
SELECT * FROM news_items LIMIT 5;
SELECT * FROM keywords;
.quit

🐛 Известные ограничения
SQLite не поддерживает UUID, используются String(36)
Redis в Windows требует Docker или WSL2
OpenAI API требует валидный ключ для реальной генерации
Telegram бот требует настройки для публикации

📄 Лицензия
MIT

✅ Проект успешно запущен и работает!
📚 Swagger UI: http://localhost:8000/docs
🏠 API Root: http://localhost:8000/
📖 ReDoc: http://localhost:8000/redoc
Спасибо за использование сервиса! 🎉
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aibot.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Telegram - с безопасным преобразованием
    TELEGRAM_API_ID = 0
    try:
        telegram_api_id = os.getenv("TELEGRAM_API_ID", "0")
        TELEGRAM_API_ID = int(telegram_api_id) if telegram_api_id and telegram_api_id.isdigit() else 0
    except (ValueError, TypeError):
        TELEGRAM_API_ID = 0

    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
    TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # App
    APP_NAME = os.getenv("APP_NAME", "AI News Bot")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    @classmethod
    def validate(cls):
        """Проверка наличия обязательных переменных (только для продакшена)"""
        if cls.DEBUG:
            # В режиме DEBUG пропускаем проверку
            return True

        # Для продакшена проверяем наличие ключей
        required_vars = ['OPENAI_API_KEY', 'TELEGRAM_API_ID', 'TELEGRAM_BOT_TOKEN']
        missing = [var for var in required_vars if not getattr(cls, var, None)]

        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")

        return True


config = Config()
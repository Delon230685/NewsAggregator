"""Конфигурация приложения"""

import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Config:
    """Конфигурация приложения"""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aibot.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Telegram
    TELEGRAM_API_ID: int = 0
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    TELEGRAM_ADMIN_ID: str = os.getenv("TELEGRAM_ADMIN_ID", "")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # App
    APP_NAME: str = os.getenv("APP_NAME", "AI News Bot")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    def __init__(self) -> None:
        """Инициализация конфигурации"""
        self._init_telegram_api_id()
        self._validate()

    def _init_telegram_api_id(self) -> None:
        """Безопасное преобразование TELEGRAM_API_ID в int"""
        telegram_api_id_str: str = os.getenv("TELEGRAM_API_ID", "0")
        try:
            self.TELEGRAM_API_ID = int(telegram_api_id_str) if telegram_api_id_str.isdigit() else 0
        except (ValueError, TypeError):
            self.TELEGRAM_API_ID = 0

    def _validate(self) -> None:
        """Проверка наличия обязательных переменных"""
        if self.DEBUG:
            return  # В DEBUG режиме не проверяем

        required_vars: dict[str, str] = {
            'OPENAI_API_KEY': self.OPENAI_API_KEY,
            'TELEGRAM_API_ID': str(self.TELEGRAM_API_ID),
            'TELEGRAM_BOT_TOKEN': self.TELEGRAM_BOT_TOKEN
        }

        missing: list[str] = [var for var, value in required_vars.items() if not value or value == "0"]

        if missing:
            print(f"Warning: Missing env vars: {', '.join(missing)}")

    def get_openai_config(self) -> dict[str, str | bool]:
        """Получить конфигурацию OpenAI"""
        return {
            "api_key": self.OPENAI_API_KEY,
            "model": self.OPENAI_MODEL,
            "is_configured": bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY != "test_key")
        }

    def get_telegram_config(self) -> dict[str, str | int | bool]:
        """Получить конфигурацию Telegram"""
        return {
            "api_id": self.TELEGRAM_API_ID,
            "api_hash": self.TELEGRAM_API_HASH,
            "bot_token": self.TELEGRAM_BOT_TOKEN,
            "channel_id": self.TELEGRAM_CHANNEL_ID,
            "is_configured": bool(
                self.TELEGRAM_API_ID and
                self.TELEGRAM_API_HASH and
                self.TELEGRAM_BOT_TOKEN and
                self.TELEGRAM_API_ID != 0
            )
        }

    def display_config(self) -> None:
        """Вывести текущую конфигурацию (без sensitive данных)"""
        print("=" * 50)
        print("Current Configuration:")
        print(f"  APP_NAME: {self.APP_NAME}")
        print(f"  DEBUG: {self.DEBUG}")
        print(f"  DATABASE_URL: {self._mask_url(self.DATABASE_URL)}")
        print(f"  OPENAI_MODEL: {self.OPENAI_MODEL}")
        print(f"  OPENAI_API_KEY: {'✓ set' if self.OPENAI_API_KEY else '✗ missing'}")
        print("=" * 50)

    @staticmethod
    def _mask_url(url: str) -> str:
        """Маскирует пароль в URL"""
        if not url:
            return "not set"
        if "redis://" in url and "@" in url:
            parts = url.split("@")
            return parts[0].split("://")[0] + "://***@" + parts[1]
        return url


# Создаем глобальный экземпляр конфигурации
config = Config()

# Выводим конфигурацию при загрузке (только в DEBUG режиме)
if config.DEBUG:
    config.display_config()
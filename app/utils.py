"""Утилиты для работы с хешами, текстом, датами, rate limiting и метриками"""

import hashlib
import re
from datetime import datetime
from typing import Any, Optional
import json
from functools import wraps
import time

from app.logger import logger


def generate_hash(text: str, max_length: int = 64) -> str:
    """
    Генерация хеша для строки (используется для дедупликации)

    Args:
        text: Исходный текст
        max_length: Максимальная длина хеша

    Returns:
        Хеш-строка
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:max_length]


def clean_text(text: str) -> str:
    """
    Очистка текста от лишних пробелов, переносов и спецсимволов

    Args:
        text: Исходный текст

    Returns:
        Очищенный текст
    """
    if not text:
        return ""

    # Удаляем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Удаляем спецсимволы (оставляем буквы, цифры, пробелы и базовую пунктуацию)
    text = re.sub(r'[^\w\s.,!?;:()-]', '', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Обрезание текста до указанной длины

    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста

    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """
    Извлечение ключевых слов из текста (простая реализация)

    Args:
        text: Исходный текст
        top_n: Количество ключевых слов для извлечения

    Returns:
        Список ключевых слов
    """
    # Стоп-слова
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'к', 'у', 'из', 'за', 'о', 'об',
        'для', 'от', 'до', 'без', 'через', 'над', 'под', 'это', 'эта',
        'этот', 'эти', 'быть', 'что', 'как', 'так', 'вот', 'там', 'тут',
        'где', 'когда', 'тогда', 'затем', 'потом', 'или', 'но', 'да',
        'нет', 'не', 'ни', 'и', 'же', 'ли', 'а', 'то', 'при', 'со'
    }

    # Токенизация и фильтрация
    words = re.findall(r'\b[а-яa-z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]

    # Подсчет частоты
    freq: dict[str, int] = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    # Сортировка и возврат топ-N
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def is_duplicate(existing_hashes: list[str], new_hash: str) -> bool:
    """
    Проверка на дубликат по хешу

    Args:
        existing_hashes: Список существующих хешей
        new_hash: Новый хеш для проверки

    Returns:
        True если дубликат, иначе False
    """
    return new_hash in existing_hashes


def format_datetime(dt: datetime, format_type: str = "full") -> str:
    """
    Форматирование даты/времени для разных нужд

    Args:
        dt: Дата/время
        format_type: Тип форматирования (full, date, time, relative)

    Returns:
        Отформатированная строка
    """
    if format_type == "full":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return dt.strftime("%Y-%m-%d")
    elif format_type == "time":
        return dt.strftime("%H:%M:%S")
    elif format_type == "relative":
        return get_relative_time(dt)
    else:
        return dt.strftime(format_type)


def get_relative_time(dt: datetime) -> str:
    """
    Получение относительного времени (например, "2 часа назад")

    Args:
        dt: Исходная дата/время

    Returns:
        Строка с относительным временем
    """
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} секунд назад"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        if minutes == 1:
            return "1 минуту назад"
        elif minutes < 5:
            return f"{minutes} минуты назад"
        else:
            return f"{minutes} минут назад"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        if hours == 1:
            return "1 час назад"
        elif hours < 5:
            return f"{hours} часа назад"
        else:
            return f"{hours} часов назад"
    else:
        days = int(seconds / 86400)
        if days == 1:
            return "1 день назад"
        elif days < 5:
            return f"{days} дня назад"
        else:
            return f"{days} дней назад"


def retry_on_failure(max_retries: int = 3, delay: int = 1, backoff: int = 2):
    """
    Декоратор для повторных попыток при ошибках

    Args:
        max_retries: Максимальное количество попыток
        delay: Начальная задержка в секундах
        backoff: Множитель увеличения задержки
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise

                    logger.warning(f"Retry {retries}/{max_retries} after error: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None

        return wrapper

    return decorator


class RateLimiter:
    """Простой rate limiter для API"""

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """
        Args:
            max_calls: Максимальное количество вызовов за окно
            time_window: Временное окно в секундах
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []

    def can_call(self) -> bool:
        """Проверка, можно ли выполнить вызов"""
        now = time.time()

        # Очищаем старые вызовы
        self.calls = [call for call in self.calls if now - call < self.time_window]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def wait_time(self) -> float:
        """Время ожидания до следующего доступного вызова"""
        if not self.calls:
            return 0

        now = time.time()
        oldest = min(self.calls)
        wait = self.time_window - (now - oldest)

        return max(0, wait)


class JSONSerializer:
    """Сериализатор для JSON с поддержкой datetime и UUID"""

    @staticmethod
    def serialize(obj: Any) -> str:
        """Сериализация объекта в JSON"""
        return json.dumps(obj, default=str, ensure_ascii=False)

    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Десериализация JSON в объект"""
        return json.loads(json_str)


def validate_url(url: str) -> bool:
    """
    Валидация URL

    Args:
        url: URL для проверки

    Returns:
        True если URL валидный, иначе False
    """
    pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # или IP
        r'(?::\d+)?'  # опциональный порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    return pattern.match(url) is not None


def safe_get(data: dict, path: str, default: Any = None) -> Any:
    """
    Безопасное получение значения из вложенного словаря

    Args:
        data: Словарь с данными
        path: Путь через точки (например, "user.address.city")
        default: Значение по умолчанию

    Returns:
        Значение из словаря или default
    """
    keys = path.split('.')
    current = data

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default

        if current is None:
            return default

    return current


def chunk_list(lst: list, chunk_size: int = 10) -> list[list]:
    """
    Разбиение списка на чанки

    Args:
        lst: Исходный список
        chunk_size: Размер чанка

    Returns:
        Список чанков
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


class MetricsCollector:
    """Сбор метрик для мониторинга"""

    def __init__(self):
        self.metrics: dict[str, int] = {
            'parsed_news': 0,
            'generated_posts': 0,
            'published_posts': 0,
            'failed_parses': 0,
            'failed_generations': 0,
            'failed_publications': 0
        }

    def increment(self, metric_name: str, value: int = 1) -> None:
        """
        Увеличение метрики

        Args:
            metric_name: Название метрики
            value: Значение для увеличения
        """
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
        else:
            logger.warning(f"Unknown metric: {metric_name}")

    def get_metrics(self) -> dict[str, int]:
        """Получение всех метрик"""
        return self.metrics.copy()

    def reset(self) -> None:
        """Сброс всех метрик"""
        for key in self.metrics:
            self.metrics[key] = 0

    def get_summary(self) -> str:
        """Получение краткой сводки метрик"""
        return (
            f"📊 Metrics: parsed={self.metrics['parsed_news']}, "
            f"generated={self.metrics['generated_posts']}, "
            f"published={self.metrics['published_posts']}, "
            f"failed={self.metrics['failed_parses'] + self.metrics['failed_generations']}"
        )


# Глобальные экземпляры
rate_limiter = RateLimiter(max_calls=30, time_window=60)
metrics_collector = MetricsCollector()
json_serializer = JSONSerializer()
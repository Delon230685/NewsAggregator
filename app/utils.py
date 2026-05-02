import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)


def generate_hash(text: str, max_length: int = 64) -> str:
    """
    Генерация хеша для строки (используется для дедупликации)
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:max_length]


def clean_text(text: str) -> str:
    """
    Очистка текста от лишних пробелов, переносов и спецсимволов
    """
    if not text:
        return ""

    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Удаляем спецсимволы (оставляем буквы, цифры, пробелы и базовую пунктуацию)
    text = re.sub(r'[^\w\s.,!?;:()-]', '', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Обрезание текста до указанной длины
    """
    if len(text) <= max_length:
        return text

    # Обрезаем по словам
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Извлечение ключевых слов из текста (простая реализация)
    """
    # Стоп-слова
    stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'из', 'за', 'о', 'об',
                  'для', 'от', 'до', 'без', 'через', 'над', 'под', 'это', 'эта',
                  'этот', 'эти', 'быть', 'что', 'как', 'так', 'вот', 'там', 'тут',
                  'где', 'когда', 'тогда', 'затем', 'потом', 'или', 'но', 'да',
                  'нет', 'не', 'ни', 'и', 'же', 'ли', 'а', 'то', 'при', 'со'}

    # Токенизация и фильтрация
    words = re.findall(r'\b[а-яa-z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]

    # Подсчет частоты
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    # Сортировка и возврат топ-N
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:top_n]]


def is_duplicate(existing_hashes: List[str], new_hash: str) -> bool:
    """
    Проверка на дубликат по хешу
    """
    return new_hash in existing_hashes


def format_datetime(dt: datetime, format_type: str = "full") -> str:
    """
    Форматирование даты/времени для разных нужд
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
    """
    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} секунд назад"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} {'минуту' if minutes == 1 else 'минуты' if minutes < 5 else 'минут'} назад"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} {'час' if hours == 1 else 'часа' if hours < 5 else 'часов'} назад"
    else:
        days = int(seconds / 86400)
        return f"{days} {'день' if days == 1 else 'дня' if days < 5 else 'дней'} назад"


def retry_on_failure(max_retries: int = 3, delay: int = 1, backoff: int = 2):
    """
    Декоратор для повторных попыток при ошибках
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
    """
    Простой rate limiter для API
    """

    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def can_call(self) -> bool:
        """
        Проверка, можно ли выполнить вызов
        """
        now = time.time()

        # Очищаем старые вызовы
        self.calls = [call for call in self.calls if now - call < self.time_window]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def wait_time(self) -> float:
        """
        Время ожидания до следующего доступного вызова
        """
        if not self.calls:
            return 0

        now = time.time()
        oldest = min(self.calls)
        wait = self.time_window - (now - oldest)

        return max(0, wait)


class JSONSerializer:
    """
    Сериализатор для JSON с поддержкой datetime и UUID
    """

    @staticmethod
    def serialize(obj: Any) -> str:
        """
        Сериализация объекта в JSON
        """
        return json.dumps(obj, default=str, ensure_ascii=False)

    @staticmethod
    def deserialize(json_str: str) -> Any:
        """
        Десериализация JSON в объект
        """
        return json.loads(json_str)


def validate_url(url: str) -> bool:
    """
    Валидация URL
    """
    pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...или IP
        r'(?::\d+)?'  # опциональный порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    return pattern.match(url) is not None


def safe_get(data: Dict, path: str, default: Any = None) -> Any:
    """
    Безопасное получение значения из вложенного словаря
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


def chunk_list(lst: List, chunk_size: int = 10) -> List[List]:
    """
    Разбиение списка на чанки
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


class MetricsCollector:
    """
    Сбор метрик для мониторинга
    """

    def __init__(self):
        self.metrics = {
            'parsed_news': 0,
            'generated_posts': 0,
            'published_posts': 0,
            'failed_parses': 0,
            'failed_generations': 0,
            'failed_publications': 0
        }

    def increment(self, metric_name: str, value: int = 1):
        """
        Увеличение метрики
        """
        if metric_name in self.metrics:
            self.metrics[metric_name] += value

    def get_metrics(self) -> Dict:
        """
        Получение всех метрик
        """
        return self.metrics.copy()

    def reset(self):
        """
        Сброс всех метрик
        """
        for key in self.metrics:
            self.metrics[key] = 0


# Глобальные экземпляры
rate_limiter = RateLimiter(max_calls=30, time_window=60)
metrics_collector = MetricsCollector()
json_serializer = JSONSerializer()
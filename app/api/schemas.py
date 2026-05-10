"""Pydantic схемы для валидации данных API"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models import SourceType, PostStatus


class NewsItemCreate(BaseModel):
    """Схема для создания новости"""
    title: str = Field(..., description="Заголовок новости", max_length=500)
    url: Optional[str] = Field(None, description="Ссылка на новость")
    summary: str = Field(..., description="Краткое содержание", max_length=1000)
    source: str = Field(..., description="Источник новости")
    raw_text: Optional[str] = Field(None, description="Полный текст новости")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Пример новости",
                "url": "https://example.com/news/1",
                "summary": "Краткое содержание новости...",
                "source": "lenta.ru",
                "raw_text": "Полный текст новости..."
            }
        }


class NewsItemResponse(BaseModel):
    """Схема ответа с данными новости"""
    id: UUID
    title: str
    url: Optional[str]
    summary: str
    source: str
    published_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Схема ответа с данными поста"""
    id: UUID
    news_id: UUID
    generated_text: str
    published_at: Optional[datetime]
    status: PostStatus

    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    """Схема для создания источника новостей"""
    type: SourceType = Field(..., description="Тип источника (site или tg)")
    name: str = Field(..., description="Название источника", max_length=200)
    url: Optional[str] = Field(None, description="URL источника (для сайтов)")
    username: Optional[str] = Field(None, description="Username в Telegram (для каналов)")
    enabled: bool = Field(True, description="Активен ли источник")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "site",
                "name": "Lenta.ru",
                "url": "https://lenta.ru",
                "enabled": True
            }
        }


class SourceResponse(BaseModel):
    """Схема ответа с данными источника"""
    id: UUID
    type: SourceType
    name: str
    url: Optional[str]
    username: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


class KeywordCreate(BaseModel):
    """Схема для создания ключевого слова"""
    word: str = Field(..., description="Ключевое слово", min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "word": "технологии"
            }
        }


class KeywordResponse(BaseModel):
    """Схема ответа с данными ключевого слова"""
    id: UUID
    word: str
    is_active: bool

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    """Схема запроса для ручной генерации поста"""
    title: str = Field(..., description="Заголовок новости", max_length=500)
    summary: str = Field(..., description="Текст новости", max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Новая технология в области ИИ",
                "summary": "Ученые представили революционную разработку..."
            }
        }


class GenerateResponse(BaseModel):
    """Схема ответа с сгенерированным постом"""
    generated_text: str = Field(..., description="Сгенерированный текст поста")


class ParseRequest(BaseModel):
    """Схема запроса для парсинга новостей"""
    source_id: Optional[UUID] = Field(None, description="ID источника (если None - все источники)")
    keywords: Optional[list[str]] = Field(None, description="Ключевые слова для фильтрации")

    class Config:
        json_schema_extra = {
            "example": {
                "keywords": ["технологии", "ИИ", "нейросети"]
            }
        }


class ParseResponse(BaseModel):
    """Схема ответа после парсинга"""
    status: str = Field(..., description="Статус выполнения (success/warning/error)")
    total_parsed: int = Field(0, description="Всего найдено новостей")
    filtered: int = Field(0, description="Отфильтровано по ключевым словам")
    new_news: int = Field(0, description="Новых новостей добавлено")
    keywords_count: int = Field(0, description="Количество активных ключевых слов")
    message: Optional[str] = Field(None, description="Дополнительное сообщение")


class StatsResponse(BaseModel):
    """Схема ответа со статистикой системы"""
    total_news: int = Field(0, description="Всего новостей")
    news_last_24h: int = Field(0, description="Новостей за последние 24 часа")
    total_posts: int = Field(0, description="Всего постов")
    published_posts: int = Field(0, description="Опубликовано постов")
    generated_posts: int = Field(0, description="Сгенерировано постов")
    failed_posts: int = Field(0, description="Постов с ошибкой")
    active_sources: int = Field(0, description="Активных источников")
    total_sources: int = Field(0, description="Всего источников")
    active_keywords: int = Field(0, description="Активных ключевых слов")
    system_status: str = Field("running", description="Статус системы")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время запроса")


class HealthResponse(BaseModel):
    """Схема ответа для проверки здоровья системы"""
    status: str = Field("ok", description="Статус API")
    database: str = Field("healthy", description="Статус базы данных")
    api_version: str = Field("1.0.0", description="Версия API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время проверки")
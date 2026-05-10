"""Модели базы данных для SQLAlchemy"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum, Integer, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.logger import logger

Base = declarative_base()


class SourceType(str, enum.Enum):
    """Типы источников новостей"""
    SITE = "site"
    TELEGRAM = "tg"


class PostStatus(str, enum.Enum):
    """Статусы постов"""
    NEW = "new"
    GENERATED = "generated"
    PUBLISHED = "published"
    FAILED = "failed"


class ParsingStatus(str, enum.Enum):
    """Статусы парсинга"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NewsItem(Base):
    """Модель новостей"""
    __tablename__ = "news_items"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    url = Column(String(1000))
    summary = Column(Text)
    source = Column(String(200), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(Text)
    hash_key = Column(String(64), unique=True, nullable=False, index=True)
    language = Column(String(10), default="ru")
    relevance_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="news", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_news_source', 'source'),
        Index('idx_news_published', 'published_at'),
        Index('idx_news_hash', 'hash_key'),
    )


class Post(Base):
    """Модель сгенерированных постов"""
    __tablename__ = "posts"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    news_id = Column(String(36), ForeignKey('news_items.id', ondelete='CASCADE'), nullable=False)
    generated_text = Column(Text)
    published_at = Column(DateTime)
    status = Column(Enum(PostStatus), default=PostStatus.NEW)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    news = relationship("NewsItem", back_populates="posts")

    __table_args__ = (
        Index('idx_posts_status', 'status'),
        Index('idx_posts_published', 'published_at'),
        Index('idx_posts_news', 'news_id'),
    )


class Source(Base):
    """Модель источников новостей"""
    __tablename__ = "sources"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(SourceType), nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(String(500))
    username = Column(String(100))
    enabled = Column(Boolean, default=True)
    last_parse_at = Column(DateTime)
    parse_interval = Column(Integer, default=1800)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sources_enabled', 'enabled'),
        Index('idx_sources_type', 'type'),
    )


class Keyword(Base):
    """Модель ключевых слов для фильтрации"""
    __tablename__ = "keywords"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_keywords_active', 'is_active'),
    )


class ParsingLog(Base):
    """Модель логов парсинга"""
    __tablename__ = "parsing_logs"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey('sources.id', ondelete='SET NULL'))
    status = Column(String(50))
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_logs_source', 'source_id'),
        Index('idx_logs_created', 'created_at'),
    )


class GenerationLog(Base):
    """Модель логов генерации постов"""
    __tablename__ = "generation_logs"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    news_id = Column(String(36), ForeignKey('news_items.id', ondelete='SET NULL'))
    post_id = Column(String(36), ForeignKey('posts.id', ondelete='SET NULL'))
    model_used = Column(String(50))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_usd = Column(Integer)
    generation_time = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_gen_news', 'news_id'),
        Index('idx_gen_created', 'created_at'),
    )


class ScheduledTask(Base):
    """Модель запланированных задач"""
    __tablename__ = "scheduled_tasks"
    __allow_unmapped__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(100), nullable=False)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_tasks_name', 'task_name'),
        Index('idx_tasks_next_run', 'next_run'),
    )
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
import sys

Base = declarative_base()


def get_uuid_column():
    """Возвращает подходящий тип для UUID в зависимости от БД"""
    if 'sqlite' in sys.argv or 'sqlite' in str(sys.argv):
        return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    else:
        return Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class SourceType(str, enum.Enum):
    SITE = "site"
    TELEGRAM = "tg"


class PostStatus(str, enum.Enum):
    NEW = "new"
    GENERATED = "generated"
    PUBLISHED = "published"
    FAILED = "failed"


class ParsingStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NewsItem(Base):
    __tablename__ = "news_items"

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
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    news_id = Column(String(36), ForeignKey('news_items.id', ondelete='CASCADE'), nullable=False)
    generated_text = Column(Text)
    published_at = Column(DateTime)
    status = Column(Enum(PostStatus), default=PostStatus.NEW)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    news = relationship("NewsItem", back_populates="posts")

    __table_args__ = (
        Index('idx_posts_status', 'status'),
        Index('idx_posts_published', 'published_at'),
        Index('idx_posts_news', 'news_id'),
    )


class Source(Base):
    __tablename__ = "sources"

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
    __tablename__ = "keywords"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_keywords_active', 'is_active'),
    )


class ParsingLog(Base):
    __tablename__ = "parsing_logs"

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
    __tablename__ = "generation_logs"

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
    __tablename__ = "scheduled_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(100), nullable=False)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_tasks_name', 'task_name'),
        Index('idx_tasks_next_run', 'next_run'),
    )
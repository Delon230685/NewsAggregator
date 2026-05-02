from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models import SourceType, PostStatus


class NewsItemCreate(BaseModel):
    title: str
    url: Optional[str] = None
    summary: str
    source: str
    raw_text: Optional[str] = None


class NewsItemResponse(BaseModel):
    id: UUID
    title: str
    url: Optional[str]
    summary: str
    source: str
    published_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: UUID
    news_id: UUID
    generated_text: str
    published_at: Optional[datetime]
    status: PostStatus

    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    type: SourceType
    name: str
    url: Optional[str] = None
    username: Optional[str] = None
    enabled: bool = True


class SourceResponse(BaseModel):
    id: UUID
    type: SourceType
    name: str
    url: Optional[str]
    username: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


class KeywordCreate(BaseModel):
    word: str


class KeywordResponse(BaseModel):
    id: UUID
    word: str
    is_active: bool

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    title: str
    summary: str


class GenerateResponse(BaseModel):
    generated_text: str
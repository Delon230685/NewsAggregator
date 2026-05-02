from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import NewsItem, Post, Source, Keyword, PostStatus
from app.api.schemas import *
# from app.tasks import generate_post_for_news_task, parse_source_task  # Временно закомментировать
from app.ai.generator import ai_generator
import asyncio

router = APIRouter(prefix="/api", tags=["API"])


# Sources endpoints
@router.get("/sources/", response_model=List[SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return sources


@router.post("/sources/", response_model=SourceResponse)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    db_source = Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.put("/sources/{source_id}", response_model=SourceResponse)
def update_source(source_id: UUID, source: SourceCreate, db: Session = Depends(get_db)):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in source.dict().items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/sources/{source_id}")
def delete_source(source_id: UUID, db: Session = Depends(get_db)):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(db_source)
    db.commit()
    return {"message": "Source deleted"}


@router.post("/sources/{source_id}/parse")
def parse_source_now(source_id: UUID, db: Session = Depends(get_db)):
    """Запустить парсинг источника вручную"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # parse_source_task.delay(str(source_id))  # Временно закомментировать
    return {"message": "Parsing started (simulated - Celery disabled for testing)"}


# Keywords endpoints
@router.get("/keywords/", response_model=List[KeywordResponse])
def get_keywords(db: Session = Depends(get_db)):
    keywords = db.query(Keyword).all()
    return keywords


@router.post("/keywords/", response_model=KeywordResponse)
def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = Keyword(**keyword.dict())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: UUID, db: Session = Depends(get_db)):
    db_keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    db.delete(db_keyword)
    db.commit()
    return {"message": "Keyword deleted"}


# Posts endpoints
@router.get("/posts/", response_model=List[PostResponse])
def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.published_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.post("/posts/{post_id}/publish")
def publish_post_manually(post_id: UUID, db: Session = Depends(get_db)):
    """Ручная публикация поста"""
    # from app.tasks import publish_post_task  # Временно закомментировать

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Post already published")

    # publish_post_task.delay(str(post_id))  # Временно закомментировать
    return {"message": "Publishing started (simulated - Celery disabled for testing)"}


# Generate endpoint
@router.post("/generate/", response_model=GenerateResponse)
async def generate_manually(request: GenerateRequest):
    """Ручная генерация поста через AI"""
    generated_text = await ai_generator.generate_post(request.title, request.summary)

    if not generated_text:
        raise HTTPException(status_code=500, detail="Generation failed")

    return GenerateResponse(generated_text=generated_text)


# News endpoints
@router.get("/news/", response_model=List[NewsItemResponse])
def get_news(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    news = db.query(NewsItem).order_by(NewsItem.published_at.desc()).offset(skip).limit(limit).all()
    return news


@router.post("/news/{news_id}/generate")
def generate_post_for_news(news_id: UUID, db: Session = Depends(get_db)):
    """Сгенерировать пост для конкретной новости"""
    news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    # generate_post_for_news_task.delay(str(news_id))  # Временно закомментировать
    return {"message": "Generation started (simulated - Celery disabled for testing)"}


# Stats endpoint
@router.get("/stats/")
def get_stats(db: Session = Depends(get_db)):
    total_news = db.query(NewsItem).count()
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
    active_sources = db.query(Source).filter(Source.enabled == True).count()

    return {
        "total_news": total_news,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "active_sources": active_sources
    }
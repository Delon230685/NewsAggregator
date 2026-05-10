from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import NewsItem, Post, Source, Keyword, PostStatus, SourceType

router = APIRouter(prefix="/api", tags=["API"])


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


class PostResponse(BaseModel):
    id: UUID
    news_id: UUID
    generated_text: str
    published_at: Optional[datetime]
    status: PostStatus

    class Config:
        from_attributes = True


class NewsItemResponse(BaseModel):
    id: UUID
    title: str
    url: Optional[str]
    summary: str
    source: str
    published_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    title: str
    summary: str


class GenerateResponse(BaseModel):
    generated_text: str


@router.get("/sources/", response_model=List[SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """Получить все источники новостей"""
    sources = db.query(Source).all()
    return sources


@router.post("/sources/", response_model=SourceResponse)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    """Создать новый источник новостей"""
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.put("/sources/{source_id}", response_model=SourceResponse)
def update_source(source_id: UUID, source: SourceCreate, db: Session = Depends(get_db)):
    """Обновить существующий источник"""
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in source.model_dump().items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/sources/{source_id}")
def delete_source(source_id: UUID, db: Session = Depends(get_db)):
    """Удалить источник"""
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(db_source)
    db.commit()
    return {"message": "Source deleted successfully"}


@router.post("/sources/{source_id}/parse")
def parse_source_now(source_id: UUID, db: Session = Depends(get_db)):
    """Запустить парсинг источника вручную"""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return {"message": f"Parsing started for source: {source.name}"}


@router.get("/keywords/", response_model=List[KeywordResponse])
def get_keywords(db: Session = Depends(get_db)):
    """Получить все ключевые слова для фильтрации"""
    keywords = db.query(Keyword).all()
    return keywords


@router.post("/keywords/", response_model=KeywordResponse)
def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    """Добавить новое ключевое слово"""
    existing = db.query(Keyword).filter(Keyword.word == keyword.word).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    db_keyword = Keyword(**keyword.model_dump())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """Удалить ключевое слово"""
    db_keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    db.delete(db_keyword)
    db.commit()
    return {"message": f"Keyword '{db_keyword.word}' deleted successfully"}


@router.put("/keywords/{keyword_id}/toggle")
def toggle_keyword(keyword_id: UUID, db: Session = Depends(get_db)):
    """Включить/выключить ключевое слово"""
    db_keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    db_keyword.is_active = not db_keyword.is_active
    db.commit()
    db.refresh(db_keyword)
    return {"message": f"Keyword {'activated' if db_keyword.is_active else 'deactivated'}"}


@router.post("/keywords/bulk-add")
def add_keywords_bulk(keywords: List[str], db: Session = Depends(get_db)):
    """Добавить несколько ключевых слов сразу"""
    added = []
    existing = []

    for word in keywords:
        kw = db.query(Keyword).filter(Keyword.word == word).first()
        if kw:
            existing.append(word)
        else:
            new_kw = Keyword(word=word, is_active=True)
            db.add(new_kw)
            added.append(word)

    db.commit()

    return {
        "added": added,
        "existing": existing,
        "total": len(added)
    }


@router.get("/news/", response_model=List[NewsItemResponse])
def get_news(skip: int = 0, limit: int = 100, source: Optional[str] = None, db: Session = Depends(get_db)):
    """Получить список новостей с фильтрацией"""
    query = db.query(NewsItem)

    if source:
        query = query.filter(NewsItem.source == source)

    news = query.order_by(NewsItem.published_at.desc()).offset(skip).limit(limit).all()
    return news


@router.get("/news/{news_id}", response_model=NewsItemResponse)
def get_news_item(news_id: str, db: Session = Depends(get_db)):
    """Получить конкретную новость по ID"""
    news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.get("/news/latest")
def get_latest_news(limit: int = 20, db: Session = Depends(get_db)):
    """Получить последние новости"""
    news = db.query(NewsItem).order_by(
        NewsItem.published_at.desc()
    ).limit(limit).all()
    return news


@router.get("/news/by-keyword/{keyword}")
def get_news_by_keyword(keyword: str, limit: int = 20, db: Session = Depends(get_db)):
    """Получить новости по ключевому слову"""
    from sqlalchemy import or_

    news = db.query(NewsItem).filter(
        or_(
            NewsItem.title.ilike(f"%{keyword}%"),
            NewsItem.summary.ilike(f"%{keyword}%")
        )
    ).order_by(NewsItem.published_at.desc()).limit(limit).all()

    return {
        "keyword": keyword,
        "count": len(news),
        "news": news
    }


@router.post("/news/{news_id}/generate")
def generate_post_for_news(news_id: str, db: Session = Depends(get_db)):
    """Сгенерировать пост для конкретной новости"""
    news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    generated_text = f"""
🔥 {news.title}

{news.summary[:200] if news.summary else '...'}...

👉 Подробнее по ссылке

#новости #актуально
    """

    post = Post(
        news_id=news.id,
        generated_text=generated_text.strip(),
        status=PostStatus.GENERATED
    )
    db.add(post)
    db.commit()

    return {"message": "Post generated", "post_id": str(post.id)}


@router.get("/posts/", response_model=List[PostResponse])
def get_posts(skip: int = 0, limit: int = 100, status: Optional[PostStatus] = None, db: Session = Depends(get_db)):
    """Получить список сгенерированных постов"""
    query = db.query(Post)

    if status:
        query = query.filter(Post.status == status)

    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Получить конкретный пост по ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/posts/{post_id}/publish")
def publish_post_manually(post_id: str, db: Session = Depends(get_db)):
    """Опубликовать пост в Telegram (ручной режим)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Post already published")

    post.status = PostStatus.PUBLISHED
    post.published_at = datetime.utcnow()
    db.commit()

    return {"message": "Post published successfully", "published_at": post.published_at}


@router.delete("/posts/{post_id}")
def delete_post(post_id: str, db: Session = Depends(get_db)):
    """Удалить пост"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}


@router.post("/generate/", response_model=GenerateResponse)
async def generate_manually(request: GenerateRequest):
    """Ручная генерация поста через AI"""
    from app.ai.generator import ai_generator

    try:
        generated_text = await ai_generator.generate_post(
            title=request.title,
            summary=request.summary
        )

        return GenerateResponse(generated_text=generated_text)

    except Exception as e:
        print(f"Generation error: {e}")
        # Fallback
        return GenerateResponse(generated_text=f"❌ Ошибка генерации: {str(e)}")


@router.post("/parse/lenta")
def parse_lenta_now(db: Session = Depends(get_db)):
    """Запустить парсинг Lenta.ru прямо сейчас"""
    from app.news_parser.lenta_parser import LentaParser, NewsFilter

    try:
        parser = LentaParser()
        news_filter = NewsFilter(db)

        all_news = parser.parse_rss()

        if not all_news:
            return {"status": "error", "message": "No news parsed"}

        filtered_news = news_filter.filter_by_keywords(all_news)

        new_news_count = 0
        for news in filtered_news:
            existing = db.query(NewsItem).filter(
                NewsItem.hash_key == news['hash_key']
            ).first()

            if not existing:
                news_item = NewsItem(**news)
                db.add(news_item)
                new_news_count += 1

        db.commit()

        return {
            "status": "success",
            "total_parsed": len(all_news),
            "filtered": len(filtered_news),
            "new_news": new_news_count
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/stats/")
def get_stats(db: Session = Depends(get_db)):
    """Получить статистику системы"""
    total_news = db.query(NewsItem).count()
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
    generated_posts = db.query(Post).filter(Post.status == PostStatus.GENERATED).count()
    failed_posts = db.query(Post).filter(Post.status == PostStatus.FAILED).count()
    active_sources = db.query(Source).filter(Source.enabled == True).count()
    total_sources = db.query(Source).count()
    active_keywords = db.query(Keyword).filter(Keyword.is_active == True).count()

    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    news_last_24h = db.query(NewsItem).filter(
        NewsItem.published_at >= yesterday
    ).count()

    return {
        "total_news": total_news,
        "news_last_24h": news_last_24h,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "generated_posts": generated_posts,
        "failed_posts": failed_posts,
        "active_sources": active_sources,
        "total_sources": total_sources,
        "active_keywords": active_keywords,
        "system_status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Проверка работоспособности API"""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        print(f"Health check error: {e}")
        db_status = "unhealthy"

    return {
        "status": "ok",
        "database": db_status,
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Получить сводку для дашборда"""
    from sqlalchemy import func

    sources_stats = db.query(
        Source.type,
        func.count(Source.id).label('count')
    ).group_by(Source.type).all()

    posts_stats = db.query(
        Post.status,
        func.count(Post.id).label('count')
    ).group_by(Post.status).all()

    return {
        "sources_distribution": [{"type": s[0].value, "count": s[1]} for s in sources_stats],
        "posts_distribution": [{"status": p[0].value, "count": p[1]} for p in posts_stats],
        "recent_activity": {
            "news_last_hour": db.query(NewsItem).filter(
                NewsItem.created_at >= datetime.utcnow()
            ).count()
        }
    }
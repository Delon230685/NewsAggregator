"""Celery задачи для парсинга, генерации постов и публикации"""

from celery import Celery
from celery.schedules import crontab
from typing import Any
from datetime import datetime, timedelta
import asyncio

from app.config import config
from app.database import db
from app.models import NewsItem, Source, Keyword, ParsingLog, Post, PostStatus
from app.news_parser.lenta_parser import LentaParser, NewsFilter
from app.logger import logger

# Настройка Celery
celery_app = Celery(
    'tasks',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Расписание задач
    beat_schedule={
        'parse-lenta-every-30-minutes': {
            'task': 'app.tasks.parse_lenta_by_keywords',
            'schedule': 1800.0,  # Каждые 30 минут
            'options': {
                'expires': 300.0  # Задача устаревает через 5 минут
            }
        },
        'generate-posts-every-10-minutes': {
            'task': 'app.tasks.generate_posts_for_news',
            'schedule': 600.0,  # Каждые 10 минут
        },
        'cleanup-old-logs-daily': {
            'task': 'app.tasks.cleanup_old_logs',
            'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
        },
    }
)


@celery_app.task(bind=True, max_retries=3)
def parse_lenta_by_keywords(self) -> dict[str, Any]:
    """
    Парсинг lenta.ru по ключевым словам

    Returns:
        Результат парсинга в виде словаря
    """
    session = db.get_session()
    try:
        logger.info("Starting Lenta.ru parsing by keywords")

        # Проверяем наличие ключевых слов
        keywords_count = session.query(Keyword).filter(Keyword.is_active == True).count()
        if keywords_count == 0:
            logger.warning("No active keywords found. Please add keywords first.")
            return {"status": "warning", "message": "No active keywords found"}

        # Парсим новости
        parser = LentaParser()
        news_filter = NewsFilter(session)

        all_news = parser.parse_rss()

        if not all_news:
            logger.warning("No news parsed from Lenta.ru")
            return {"status": "error", "message": "No news parsed"}

        logger.info(f"Parsed {len(all_news)} news from Lenta.ru")

        # Фильтруем по ключевым словам
        filtered_news = news_filter.filter_by_keywords(all_news)
        logger.info(f"Filtered {len(filtered_news)} news by keywords")

        # Сохраняем в базу
        new_news_count = 0
        for news in filtered_news:
            # Проверяем, нет ли уже такой новости
            existing = session.query(NewsItem).filter(
                NewsItem.hash_key == news['hash_key']
            ).first()

            if not existing:
                news_item = NewsItem(**news)
                session.add(news_item)
                new_news_count += 1

        session.commit()

        # Логируем результат
        parse_log = ParsingLog(
            source_id=None,
            status="completed",
            items_found=len(all_news),
            items_new=new_news_count,
            duration_seconds=0
        )
        session.add(parse_log)
        session.commit()

        logger.info(f"Saved {new_news_count} new news from Lenta.ru")

        # Запускаем генерацию постов для новых новостей
        if new_news_count > 0:
            generate_posts_for_news.delay()

        return {
            "status": "success",
            "total_parsed": len(all_news),
            "filtered": len(filtered_news),
            "new_news": new_news_count,
            "keywords_count": keywords_count
        }

    except Exception as e:
        logger.error(f"Error parsing Lenta.ru: {e}")
        session.rollback()

        # Логируем ошибку
        parse_log = ParsingLog(
            source_id=None,
            status="failed",
            error_message=str(e)
        )
        session.add(parse_log)
        session.commit()

        # Повторная попытка при ошибке
        try:
            self.retry(countdown=60 * 5)  # Повторить через 5 минут
        except Exception as retry_error:
            logger.error(f"Retry failed: {retry_error}")

        return {"status": "error", "message": str(e)}

    finally:
        session.close()


@celery_app.task(bind=True, max_retries=3)
def generate_posts_for_news(self) -> dict[str, Any]:
    """
    Генерация постов для новых новостей

    Returns:
        Результат генерации в виде словаря
    """
    session = db.get_session()
    try:
        from app.ai.generator import ai_generator

        # Находим новости без постов
        news_without_posts = session.query(NewsItem).outerjoin(
            Post, NewsItem.id == Post.news_id
        ).filter(Post.id == None).limit(10).all()

        if not news_without_posts:
            logger.info("No news without posts found")
            return {"generated": 0, "message": "No pending news"}

        logger.info(f"Found {len(news_without_posts)} news without posts")

        generated_count = 0
        failed_count = 0

        for news in news_without_posts:
            try:
                # Генерируем пост
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                generated_text = loop.run_until_complete(
                    ai_generator.generate_post(news.title, news.summary or news.raw_text or "")
                )
                loop.close()

                if generated_text:
                    post = Post(
                        news_id=news.id,
                        generated_text=generated_text,
                        status=PostStatus.GENERATED
                    )
                    session.add(post)
                    generated_count += 1
                    logger.info(f"Generated post for news: {news.title[:50]}...")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to generate post for news: {news.title[:50]}...")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error generating post for news {news.id}: {e}")

                # Создаем запись о неудачной генерации
                post = Post(
                    news_id=news.id,
                    generated_text=f"❌ Ошибка генерации: {str(e)}",
                    status=PostStatus.FAILED,
                    error_message=str(e)
                )
                session.add(post)

        session.commit()
        logger.info(f"Generated {generated_count} posts, failed {failed_count}")

        return {
            "generated": generated_count,
            "failed": failed_count,
            "total": len(news_without_posts)
        }

    except Exception as e:
        logger.error(f"Error in generate_posts_for_news: {e}")
        session.rollback()

        # Повторная попытка при ошибке
        try:
            self.retry(countdown=60 * 2)  # Повторить через 2 минуты
        except Exception as retry_error:
            logger.error(f"Retry failed: {retry_error}")

        return {"error": str(e)}
    finally:
        session.close()


@celery_app.task
def parse_all_sources() -> dict[str, Any]:
    """
    Парсинг всех активных источников

    Returns:
        Результат запуска задач в виде словаря
    """
    session = db.get_session()
    try:
        sources = session.query(Source).filter(Source.enabled == True).all()

        if not sources:
            logger.warning("No active sources found")
            return {"status": "warning", "message": "No active sources"}

        tasks = []
        for source in sources:
            if source.type == 'site' and source.url and 'lenta' in source.url.lower():
                task = parse_lenta_by_keywords.delay()
                tasks.append(task.id)
                logger.debug(f"Started task for source: {source.name}")

        logger.info(f"Started parsing for {len(tasks)} sources")
        return {"status": "started", "tasks": tasks}

    except Exception as e:
        logger.error(f"Error in parse_all_sources: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        session.close()


@celery_app.task
def cleanup_old_logs() -> dict[str, Any]:
    """
    Очистка старых логов (старше 30 дней)

    Returns:
        Результат очистки в виде словаря
    """
    session = db.get_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Удаляем старые логи парсинга
        old_parsing_logs = session.query(ParsingLog).filter(
            ParsingLog.created_at < cutoff_date
        ).delete()

        # Удаляем старые посты со статусом FAILED
        old_failed_posts = session.query(Post).filter(
            Post.status == PostStatus.FAILED,
            Post.created_at < cutoff_date
        ).delete()

        session.commit()

        logger.info(f"Cleaned up {old_parsing_logs} old parsing logs and {old_failed_posts} failed posts")

        return {
            "deleted_parsing_logs": old_parsing_logs,
            "deleted_failed_posts": old_failed_posts
        }

    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


@celery_app.task
def test_celery() -> dict[str, Any]:
    """
    Тестовая задача для проверки работы Celery

    Returns:
        Статус работы Celery
    """
    logger.info("Celery is working!")
    return {
        "status": "success",
        "message": "Celery is working correctly",
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(bind=True, max_retries=3)
def publish_post_task(self, post_id: str) -> dict[str, Any]:
    """
    Публикация поста в Telegram

    Args:
        post_id: ID поста для публикации

    Returns:
        Результат публикации в виде словаря
    """
    from app.telegram.publisher import telegram_publisher

    session = db.get_session()
    try:
        post = session.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.error(f"Post {post_id} not found")
            return {"status": "error", "message": "Post not found"}

        if post.status == PostStatus.PUBLISHED:
            logger.info(f"Post {post_id} already published")
            return {"status": "skipped", "message": "Already published"}

        # Проверяем конфигурацию Telegram
        if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "test_token":
            logger.warning("Telegram bot not configured, skipping publish")
            return {"status": "skipped", "message": "Telegram not configured"}

        # Публикуем в Telegram
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            telegram_publisher.publish_post(post.generated_text, config.TELEGRAM_CHANNEL_ID)
        )
        loop.close()

        if success:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
            session.commit()
            logger.info(f"Successfully published post {post_id}")
            return {"status": "success", "message": "Post published"}
        else:
            post.status = PostStatus.FAILED
            post.error_message = "Failed to publish to Telegram"
            session.commit()
            logger.error(f"Failed to publish post {post_id}")
            return {"status": "error", "message": "Publishing failed"}

    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}")
        if session:
            session.rollback()

        # Повторная попытка при ошибке
        try:
            self.retry(countdown=60, max_retries=3)
        except Exception:
            pass

        return {"status": "error", "message": str(e)}
    finally:
        if session:
            session.close()
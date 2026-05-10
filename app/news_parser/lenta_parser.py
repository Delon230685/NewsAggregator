"""Парсер новостей с Lenta.ru"""

from datetime import datetime
from typing import Any, Optional
import hashlib
import re

import feedparser

from app.logger import logger


class LentaParser:
    """Парсер новостей с lenta.ru"""

    def __init__(self) -> None:
        """Инициализация парсера Lenta.ru"""
        self.base_url: str = "https://lenta.ru"
        self.rss_url: str = "https://lenta.ru/rss"
        self.headers: dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.debug("LentaParser initialized")

    def parse_rss(self) -> list[dict[str, Any]]:
        """
        Парсинг RSS ленты lenta.ru

        Returns:
            Список новостей в виде словарей
        """
        try:
            feed = feedparser.parse(self.rss_url)
            news_items: list[dict[str, Any]] = []

            for entry in feed.entries[:30]:  # Берем последние 30 новостей
                # Извлекаем текст из описания
                summary: str = entry.get('summary', '')
                # Очищаем от HTML тегов
                summary = re.sub(r'<[^>]+>', '', summary)

                # Парсим дату
                published_at: datetime = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # Создаем хеш для дедупликации
                hash_key: str = hashlib.md5(f"{entry.title}{entry.link}".encode()).hexdigest()

                news_items.append({
                    'title': entry.title,
                    'url': entry.link,
                    'summary': summary[:500],
                    'source': 'lenta.ru',
                    'published_at': published_at,
                    'raw_text': summary,
                    'hash_key': hash_key
                })

            logger.info(f"Parsed {len(news_items)} news from Lenta.ru RSS")
            return news_items

        except Exception as e:
            logger.error(f"Error parsing Lenta.ru RSS: {e}")
            return []

    def parse_by_keywords(self, keywords: list[str]) -> list[dict[str, Any]]:
        """
        Парсинг новостей по ключевым словам

        Args:
            keywords: Список ключевых слов для фильтрации

        Returns:
            Список новостей, содержащих ключевые слова
        """
        all_news: list[dict[str, Any]] = self.parse_rss()
        filtered_news: list[dict[str, Any]] = []

        for news in all_news:
            text_to_check: str = (news['title'] + " " + news['summary']).lower()

            for keyword in keywords:
                if keyword.lower() in text_to_check:
                    filtered_news.append(news)
                    break

        logger.info(f"Filtered {len(filtered_news)} news by {len(keywords)} keywords")
        return filtered_news


class NewsFilter:
    """Фильтр новостей по ключевым словам из базы данных"""

    def __init__(self, db_session):
        """
        Инициализация фильтра

        Args:
            db_session: Сессия базы данных SQLAlchemy
        """
        self.db_session = db_session
        logger.debug("NewsFilter initialized")

    def filter_by_keywords(self, news_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Фильтрация новостей по ключевым словам из БД

        Args:
            news_items: Список новостей для фильтрации

        Returns:
            Отфильтрованный список новостей
        """
        from app.models import Keyword

        # Получаем активные ключевые слова из БД
        keywords = self.db_session.query(Keyword).filter(
            Keyword.is_active == True
        ).all()

        if not keywords:
            logger.warning("No active keywords found in database")
            return news_items

        keyword_list: list[str] = [kw.word.lower() for kw in keywords]
        filtered_news: list[dict[str, Any]] = []

        for news in news_items:
            text_to_check: str = (
                (news.get('title', '') + " " + news.get('summary', '')).lower()
            )

            for keyword in keyword_list:
                if keyword in text_to_check:
                    filtered_news.append(news)
                    logger.debug(f"News matched keyword '{keyword}': {news['title'][:50]}...")
                    break

        logger.info(
            f"Filtered {len(filtered_news)}/{len(news_items)} news "
            f"by {len(keyword_list)} keywords"
        )
        return filtered_news

    def calculate_relevance_score(
            self,
            news_item: dict[str, Any],
            keywords: list[str]
    ) -> int:
        """
        Расчет релевантности новости (0-100)

        Args:
            news_item: Словарь с данными новости
            keywords: Список ключевых слов

        Returns:
            Оценка релевантности от 0 до 100
        """
        text: str = (
            (news_item.get('title', '') + " " + news_item.get('summary', '')).lower()
        )

        total_score: int = 0
        for keyword in keywords:
            if keyword.lower() in text:
                # За каждое вхождение +20 баллов
                total_score += 20

        # Ограничиваем 100
        return min(total_score, 100)

    def get_matched_keywords(
            self,
            news_item: dict[str, Any],
            keywords: list[str]
    ) -> list[str]:
        """
        Получить список ключевых слов, найденных в новости

        Args:
            news_item: Словарь с данными новости
            keywords: Список ключевых слов для проверки

        Returns:
            Список найденных ключевых слов
        """
        text: str = (
            (news_item.get('title', '') + " " + news_item.get('summary', '')).lower()
        )

        matched: list[str] = []
        for keyword in keywords:
            if keyword.lower() in text:
                matched.append(keyword)

        return matched
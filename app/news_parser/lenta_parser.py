from datetime import datetime
from typing import List, Dict
import hashlib
import re
import logging

logger = logging.getLogger(__name__)


class LentaParser:
    """Парсер новостей с lenta.ru"""

    def __init__(self):
        self.base_url = "https://lenta.ru"
        self.rss_url = "https://lenta.ru/rss"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def parse_rss(self) -> List[Dict]:
        """Парсинг RSS ленты lenta.ru"""
        try:
            import feedparser
            feed = feedparser.parse(self.rss_url)
            news_items = []

            for entry in feed.entries[:30]:
                summary = entry.get('summary', '')
                summary = re.sub(r'<[^>]+>', '', summary)

                published_at = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                hash_key = hashlib.md5(f"{entry.title}{entry.link}".encode()).hexdigest()

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

    def parse_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Парсинг новостей по ключевым словам"""
        all_news = self.parse_rss()
        filtered_news = []

        for news in all_news:
            text_to_check = (news['title'] + " " + news['summary']).lower()

            for keyword in keywords:
                if keyword.lower() in text_to_check:
                    filtered_news.append(news)
                    break

        logger.info(f"Filtered {len(filtered_news)} news by keywords: {keywords}")
        return filtered_news


class NewsFilter:
    """Фильтр новостей по ключевым словам"""

    def __init__(self, db_session):
        self.db_session = db_session

    def filter_by_keywords(self, news_items: List[Dict]) -> List[Dict]:
        """Фильтрация новостей по ключевым словам из БД"""
        from app.models import Keyword

        keywords = self.db_session.query(Keyword).filter(
            Keyword.is_active == True
        ).all()

        if not keywords:
            logger.warning("No keywords found in database")
            return news_items

        keyword_list = [kw.word for kw in keywords]
        filtered_news = []

        for news in news_items:
            text_to_check = (news.get('title', '') + " " + news.get('summary', '')).lower()

            for keyword in keyword_list:
                if keyword.lower() in text_to_check:
                    filtered_news.append(news)
                    logger.debug(f"News matched keyword '{keyword}': {news['title'][:50]}")
                    break

        logger.info(f"Filtered {len(filtered_news)}/{len(news_items)} news by {len(keyword_list)} keywords")
        return filtered_news

    def calculate_relevance_score(self, news_item: Dict, keywords: List[str]) -> int:
        """Расчет релевантности новости (0-100)"""
        text = (news_item.get('title', '') + " " + news_item.get('summary', '')).lower()

        total_score = 0
        for keyword in keywords:
            if keyword.lower() in text:
                # За каждое вхождение +20 баллов
                total_score += 20

        return min(total_score, 100)
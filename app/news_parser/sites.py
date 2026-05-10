"""Парсер новостей с сайтов (RSS и HTML)"""

import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from typing import Any
import hashlib

from app.logger import logger


class SiteParser:
    """Парсер новостей с сайтов через RSS или HTML"""

    @staticmethod
    def parse_rss(url: str) -> list[dict[str, Any]]:
        """
        Парсинг RSS ленты

        Args:
            url: URL RSS ленты

        Returns:
            Список новостей в виде словарей
        """
        try:
            feed = feedparser.parse(url)
            news_items: list[dict[str, Any]] = []

            for entry in feed.entries[:10]:  # Берем последние 10 записей
                title: str = entry.get('title', '')
                summary: str = entry.get('summary', '') or entry.get('description', '')
                link: str = entry.get('link', '')
                published = entry.get('published_parsed')

                if published:
                    published_at: datetime = datetime(*published[:6])
                else:
                    published_at: datetime = datetime.utcnow()

                # Создаем хеш для дедупликации
                hash_key: str = hashlib.sha256(f"{title}{link}".encode()).hexdigest()

                news_items.append({
                    'title': title,
                    'url': link,
                    'summary': summary[:500],
                    'source': url,
                    'published_at': published_at,
                    'raw_text': summary,
                    'hash_key': hash_key
                })

            logger.info(f"Parsed {len(news_items)} news from RSS: {url}")
            return news_items

        except Exception as e:
            logger.error(f"Error parsing RSS {url}: {e}")
            return []

    @staticmethod
    def parse_html(url: str) -> list[dict[str, Any]]:
        """
        Парсинг HTML страницы

        Args:
            url: URL HTML страницы

        Returns:
            Список новостей в виде словарей
        """
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()  # Проверяем статус ответа

            soup = BeautifulSoup(response.content, 'html.parser')
            news_items: list[dict[str, Any]] = []

            # Ищем типичные элементы новостей
            articles = soup.find_all(['article', '.news-item', '.post'], limit=10)

            for article in articles:
                # Поиск заголовка
                title_elem = article.find(['h1', 'h2', 'h3', '.title', '.news-title'])
                title: str = title_elem.get_text(strip=True) if title_elem else ''

                # Поиск краткого описания
                summary_elem = article.find(['p', '.description', '.summary', '.announce'])
                summary: str = summary_elem.get_text(strip=True) if summary_elem else ''

                # Поиск ссылки
                link_elem = article.find('a')
                link: str = link_elem.get('href') if link_elem else ''
                if link and not link.startswith('http'):
                    # Относительная ссылка - добавляем базовый URL
                    base_url = '/'.join(url.split('/')[:3])  # протокол://домен
                    link = base_url + '/' + link.lstrip('/')

                # Сохраняем только если есть заголовок и содержание
                if title and summary:
                    hash_key: str = hashlib.sha256(f"{title}{link}".encode()).hexdigest()
                    news_items.append({
                        'title': title,
                        'url': link,
                        'summary': summary[:500],
                        'source': url,
                        'published_at': datetime.utcnow(),
                        'raw_text': summary,
                        'hash_key': hash_key
                    })

            logger.info(f"Parsed {len(news_items)} news from HTML: {url}")
            return news_items

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error parsing HTML {url}")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error parsing HTML {url}")
            return []
        except Exception as e:
            logger.error(f"Error parsing HTML {url}: {e}")
            return []

    @staticmethod
    def parse_auto(url: str) -> list[dict[str, Any]]:
        """
        Автоматическое определение типа источника (RSS или HTML)

        Args:
            url: URL для парсинга

        Returns:
            Список новостей в виде словарей
        """
        # Проверяем, является ли URL RSS лентой
        if 'rss' in url.lower() or 'feed' in url.lower() or url.endswith('.xml'):
            logger.debug(f"Detected RSS feed: {url}")
            return SiteParser.parse_rss(url)
        else:
            logger.debug(f"Detected HTML page: {url}")
            return SiteParser.parse_html(url)
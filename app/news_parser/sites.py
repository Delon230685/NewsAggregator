import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from typing import List, Dict
import hashlib


class SiteParser:
    @staticmethod
    def parse_rss(url: str) -> List[Dict]:
        """Парсинг RSS ленты"""
        try:
            feed = feedparser.parse(url)
            news_items = []

            for entry in feed.entries[:10]:  # Берем последние 10
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                published = entry.get('published_parsed')

                if published:
                    published_at = datetime(*published[:6])
                else:
                    published_at = datetime.utcnow()

                # Создаем хеш для дедупликации
                hash_key = hashlib.sha256(f"{title}{link}".encode()).hexdigest()

                news_items.append({
                    'title': title,
                    'url': link,
                    'summary': summary[:500],  # Ограничиваем длину
                    'source': url,
                    'published_at': published_at,
                    'raw_text': summary,
                    'hash_key': hash_key
                })

            return news_items
        except Exception as e:
            print(f"Error parsing RSS {url}: {e}")
            return []

    @staticmethod
    def parse_html(url: str) -> List[Dict]:
        """Парсинг HTML страницы"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем типичные элементы новостей
            news_items = []
            articles = soup.find_all(['article', '.news-item', '.post'], limit=10)

            for article in articles:
                title_elem = article.find(['h1', 'h2', 'h3', '.title'])
                title = title_elem.get_text(strip=True) if title_elem else ''

                summary_elem = article.find(['p', '.description', '.summary'])
                summary = summary_elem.get_text(strip=True) if summary_elem else ''

                link_elem = article.find('a')
                link = link_elem.get('href') if link_elem else ''
                if link and not link.startswith('http'):
                    link = url.rstrip('/') + '/' + link.lstrip('/')

                if title and summary:
                    hash_key = hashlib.sha256(f"{title}{link}".encode()).hexdigest()
                    news_items.append({
                        'title': title,
                        'url': link,
                        'summary': summary[:500],
                        'source': url,
                        'published_at': datetime.utcnow(),
                        'raw_text': summary,
                        'hash_key': hash_key
                    })

            return news_items
        except Exception as e:
            print(f"Error parsing HTML {url}: {e}")
            return []
"""Тестовый скрипт для парсинга Lenta.ru"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.news_parser.lenta_parser import LentaParser
from app.database import db
from app.models import Keyword

def test_parse():
    print("🚀 Starting Lenta.ru parser test...")
    
    parser = LentaParser()
    news_items = parser.parse_rss()
    print(f"✅ Parsed {len(news_items)} news")
    
    print("\n📰 Latest news:")
    for i, news in enumerate(news_items[:5], 1):
        print(f"{i}. {news['title']}")
        print(f"   URL: {news['url']}")
        print()
    
    session = db.get_session()
    keywords = session.query(Keyword).filter(Keyword.is_active == True).all()
    keyword_list = [kw.word for kw in keywords]
    print(f"🔑 Active keywords: {', '.join(keyword_list) if keyword_list else 'No keywords found!'}")
    session.close()

if __name__ == "__main__":
    test_parse()

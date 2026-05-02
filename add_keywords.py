"""
Скрипт для добавления начальных ключевых слов
Запустите: python add_keywords.py
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import db
from app.models import Keyword


def add_keywords():
    session = db.get_session()

    # Список ключевых слов для фильтрации
    keywords_list = [
        "Россия",
        "Путин",
        "война",
        "экономика",
        "IT",
        "технологии",
        "искусственный интеллект",
        "нейросети",
        "космос",
        "наука",
        "медицина",
        "политика",
        "выборы",
        "санкции",
        "бизнес",
        "стартап",
        "инвестиции"
    ]

    added = []
    for word in keywords_list:
        existing = session.query(Keyword).filter(Keyword.word == word).first()
        if not existing:
            kw = Keyword(word=word, is_active=True)
            session.add(kw)
            added.append(word)

    session.commit()
    print(f"✅ Added {len(added)} keywords: {', '.join(added)}")

    # Показываем все ключевые слова
    all_keywords = session.query(Keyword).all()
    print(f"\n📋 Total keywords in database: {len(all_keywords)}")
    for kw in all_keywords:
        print(f"  - {kw.word} (active: {kw.is_active})")

    session.close()


if __name__ == "__main__":
    add_keywords()
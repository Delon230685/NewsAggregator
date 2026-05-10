import sqlite3

conn = sqlite3.connect('aibot.db')
cursor = conn.cursor()

print("="*60)
print("📊 БАЗА ДАННЫХ aibot.db")
print("="*60)

# 1. Все таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print("\n📋 ТАБЛИЦЫ:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"   - {table[0]} ({count} записей)")

# 2. Ключевые слова
cursor.execute("SELECT word, is_active FROM keywords;")
keywords = cursor.fetchall()
print(f"\n🔑 КЛЮЧЕВЫЕ СЛОВА (всего: {len(keywords)}):")
for word, active in keywords:
    status = "активно" if active else "неактивно"
    print(f"   - {word} ({status})")

# 3. Статистика
cursor.execute("SELECT COUNT(*) FROM news_items;")
news_count = cursor.fetchone()[0]
print(f"\n📰 НОВОСТЕЙ В БАЗЕ: {news_count}")

cursor.execute("SELECT COUNT(*) FROM posts;")
posts_count = cursor.fetchone()[0]
print(f"📝 ПОСТОВ В БАЗЕ: {posts_count}")

# 4. Статусы постов
cursor.execute("SELECT status, COUNT(*) FROM posts GROUP BY status;")
post_statuses = cursor.fetchall()
if post_statuses:
    print(f"\n📊 СТАТУСЫ ПОСТОВ:")
    for status, count in post_statuses:
        print(f"   - {status}: {count}")

# 5. Последние 3 новости
cursor.execute("SELECT title, source, published_at FROM news_items ORDER BY published_at DESC LIMIT 3;")
latest = cursor.fetchall()
if latest:
    print(f"\n🆕 ПОСЛЕДНИЕ 3 НОВОСТИ:")
    for i, news in enumerate(latest, 1):
        title = news[0][:60] + "..." if len(news[0]) > 60 else news[0]
        print(f"   {i}. {title}")
        print(f"      Источник: {news[1]}")
        print(f"      Дата: {news[2]}")

conn.close()
print("\n" + "="*60)
print("✅ Готово!")
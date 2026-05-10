from telethon import TelegramClient
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib
from app.config import config


class TelegramParser:
    def __init__(self):
        self.client = TelegramClient(
            'session',
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH
        )

    async def parse_channel(self, channel_username: str, limit: int = 20) -> List[Dict]:
        """Парсинг Telegram канала"""
        news_items = []

        await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)

        try:
            channel = await self.client.get_entity(channel_username)

            since = datetime.utcnow() - timedelta(hours=6)

            async for message in self.client.iter_messages(channel, limit=limit):
                if message.date.replace(tzinfo=None) < since:
                    break

                if message.text:
                    title = message.text[:100]

                    hash_key = hashlib.sha256(f"{message.id}{channel_username}".encode()).hexdigest()

                    news_items.append({
                        'title': title,
                        'url': f"https://t.me/{channel_username}/{message.id}",
                        'summary': message.text[:500],
                        'source': f"tg://{channel_username}",
                        'published_at': message.date.replace(tzinfo=None),
                        'raw_text': message.text,
                        'hash_key': hash_key
                    })
        except Exception as e:
            print(f"Error parsing Telegram channel {channel_username}: {e}")
        finally:
            await self.client.disconnect()

        return news_items
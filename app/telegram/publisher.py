from telethon import TelegramClient
from app.config import config
import logging


class TelegramPublisher:
    def __init__(self):
        self.client = TelegramClient('publisher_session', config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)

    async def publish_post(self, text: str, channel_id: str) -> bool:
        """Публикация поста в Telegram канал"""
        try:
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)

            channel = await self.client.get_entity(channel_id)

            if len(text) > 4096:
                text = text[:4093] + "..."

            await self.client.send_message(channel, text)
            logging.info(f"Successfully published post to {channel_id}")
            return True

        except Exception as e:
            logging.error(f"Error publishing post: {e}")
            return False
        finally:
            await self.client.disconnect()

    async def check_if_published(self, news_hash: str) -> bool:
        """Проверка, не опубликован ли уже пост"""
        return False


telegram_publisher = TelegramPublisher()
"""Публикатор постов в Telegram"""

from telethon import TelegramClient
from typing import Optional

from app.config import config
from app.logger import logger


class TelegramPublisher:
    """Публикатор постов в Telegram канал"""

    def __init__(self) -> None:
        """Инициализация публикатора"""
        self.client: Optional[TelegramClient] = None
        if self._is_configured():
            self._init_client()
        else:
            logger.warning("Telegram not configured. Publishing disabled.")

    def _is_configured(self) -> bool:
        """Проверка конфигурации Telegram"""
        return bool(
            config.TELEGRAM_API_ID and
            config.TELEGRAM_API_ID != 0 and
            config.TELEGRAM_API_HASH and
            config.TELEGRAM_API_HASH != "test_hash" and
            config.TELEGRAM_BOT_TOKEN and
            config.TELEGRAM_BOT_TOKEN != "test_token" and
            config.TELEGRAM_CHANNEL_ID and
            config.TELEGRAM_CHANNEL_ID != "@test_channel"
        )

    def _init_client(self) -> None:
        """Инициализация клиента Telegram"""
        try:
            self.client = TelegramClient(
                'publisher_session',
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            logger.debug("Telegram publisher client created")
        except Exception as e:
            logger.error(f"Failed to create Telegram client: {e}")
            self.client = None

    async def publish_post(self, text: str, channel_id: str) -> bool:
        """Публикация поста в Telegram канал"""
        if not self.client:
            logger.error("Telegram client not initialized")
            return False

        if not text:
            logger.error("Cannot publish empty post")
            return False

        try:
            logger.info(f"Publishing post to channel: {channel_id}")
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)

            channel = await self.client.get_entity(channel_id)

            # Проверяем длину сообщения (ограничение Telegram 4096 символов)
            if len(text) > 4096:
                text = text[:4093] + "..."
                logger.warning(f"Post truncated to {len(text)} chars")

            await self.client.send_message(channel, text)
            logger.info(f"Successfully published post to {channel_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing post: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()
                logger.debug("Telegram client disconnected")

    async def check_if_published(self, news_hash: str) -> bool:
        """Проверка, не опубликован ли уже пост"""
        # TODO: Реализовать проверку через Redis или БД
        logger.debug(f"Checking if post with hash {news_hash} is published")
        return False

    async def test_connection(self) -> bool:
        """Тестирование подключения к Telegram API"""
        if not self.client:
            logger.error("Telegram client not initialized")
            return False

        try:
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)
            logger.info("Telegram API connection successful")
            return True
        except Exception as e:
            logger.error(f"Telegram API connection failed: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()


# Глобальный экземпляр публикатора
telegram_publisher = TelegramPublisher()
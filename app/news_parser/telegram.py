"""Парсер новостей из Telegram каналов"""

from telethon import TelegramClient
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib

from app.config import config
from app.logger import logger


class TelegramParser:
    """Парсер новостей из Telegram каналов"""

    def __init__(self) -> None:
        """Инициализация парсера Telegram"""
        self.client: Optional[TelegramClient] = None
        self._init_client()
        logger.debug("TelegramParser initialized")

    def _init_client(self) -> None:
        """Инициализация клиента Telegram"""
        if not self._is_configured():
            logger.warning("Telegram API not configured. Telegram parsing will be disabled.")
            self.client = None
            return

        try:
            self.client = TelegramClient(
                'session',
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            logger.debug("Telegram client created")
        except Exception as e:
            logger.error(f"Failed to create Telegram client: {e}")
            self.client = None

    def _is_configured(self) -> bool:
        """
        Проверка наличия конфигурации Telegram

        Returns:
            True если API настроен, иначе False
        """
        return (
                config.TELEGRAM_API_ID != 0 and
                config.TELEGRAM_API_ID is not None and
                config.TELEGRAM_API_HASH and
                config.TELEGRAM_API_HASH != "test_hash" and
                config.TELEGRAM_BOT_TOKEN and
                config.TELEGRAM_BOT_TOKEN != "test_token"
        )

    async def parse_channel(
            self,
            channel_username: str,
            limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Парсинг Telegram канала

        Args:
            channel_username: Username канала (например, 'channel_name')
            limit: Максимальное количество сообщений для парсинга

        Returns:
            Список новостей в виде словарей
        """
        if not self.client:
            logger.error("Telegram client not initialized. Check your API credentials.")
            return []

        if not channel_username:
            logger.error("Channel username is required")
            return []

        news_items: list[dict[str, Any]] = []

        try:
            logger.info(f"Starting parse of Telegram channel: {channel_username}")
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)

            # Получаем информацию о канале
            channel = await self.client.get_entity(channel_username)
            logger.debug(f"Connected to channel: {channel.title if hasattr(channel, 'title') else channel_username}")

            # Ограничиваем период - только за последние 6 часов
            since: datetime = datetime.utcnow() - timedelta(hours=6)
            messages_processed: int = 0

            async for message in self.client.iter_messages(channel, limit=limit):
                # Проверяем время сообщения
                if message.date.replace(tzinfo=None) < since:
                    logger.debug(f"Stopping parse - message older than 6 hours")
                    break

                if message.text:
                    messages_processed += 1
                    title: str = message.text[:100]

                    # Создаем хеш для дедупликации
                    hash_key: str = hashlib.sha256(
                        f"{message.id}{channel_username}".encode()
                    ).hexdigest()

                    news_items.append({
                        'title': title,
                        'url': f"https://t.me/{channel_username}/{message.id}",
                        'summary': message.text[:500],
                        'source': f"tg://{channel_username}",
                        'published_at': message.date.replace(tzinfo=None),
                        'raw_text': message.text,
                        'hash_key': hash_key
                    })

                    logger.debug(f"Processed message {message.id} from {channel_username}")

            logger.info(
                f"Parsed {len(news_items)} news from Telegram channel {channel_username} "
                f"(processed {messages_processed} messages)"
            )

        except Exception as e:
            logger.error(f"Error parsing Telegram channel {channel_username}: {e}")
        finally:
            if self.client:
                await self.client.disconnect()
                logger.debug("Telegram client disconnected")

        return news_items

    async def parse_multiple_channels(
            self,
            channels: list[str],
            limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Парсинг нескольких Telegram каналов

        Args:
            channels: Список username каналов
            limit: Максимальное количество сообщений на канал

        Returns:
            Список новостей из всех каналов
        """
        all_news: list[dict[str, Any]] = []

        for channel in channels:
            try:
                news = await self.parse_channel(channel, limit)
                all_news.extend(news)
                logger.debug(f"Parsed {len(news)} news from {channel}")
            except Exception as e:
                logger.error(f"Failed to parse channel {channel}: {e}")
                continue

        logger.info(f"Total parsed news from {len(channels)} channels: {len(all_news)}")
        return all_news

    async def test_connection(self) -> bool:
        """
        Тестирование подключения к Telegram API

        Returns:
            True если подключение успешно, иначе False
        """
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
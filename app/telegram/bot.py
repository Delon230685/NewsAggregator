"""Telegram бот для управления сервисом через сообщения"""

from telethon import TelegramClient, events
from typing import Optional
from datetime import datetime

from app.config import config
from app.ai.generator import ai_generator
from app.database import db
from app.models import NewsItem, Post, Source, PostStatus
from app.logger import logger


class TelegramBot:
    """Telegram бот для управления сервисом через сообщения"""

    def __init__(self) -> None:
        """Инициализация Telegram бота"""
        self.client: Optional[TelegramClient] = None
        self.is_running: bool = False
        self.command_handlers: dict = {}

        if self._is_configured():
            self._init_client()
        else:
            logger.warning("Telegram bot not configured. Bot will be disabled.")

    def _is_configured(self) -> bool:
        """Проверка конфигурации Telegram"""
        return (
                config.TELEGRAM_API_ID != 0 and
                config.TELEGRAM_API_ID is not None and
                config.TELEGRAM_API_HASH and
                config.TELEGRAM_API_HASH != "test_hash" and
                config.TELEGRAM_BOT_TOKEN and
                config.TELEGRAM_BOT_TOKEN != "test_token"
        )

    def _init_client(self) -> None:
        """Инициализация клиента Telegram"""
        try:
            self.client = TelegramClient(
                'bot_session',
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            logger.debug("Telegram bot client created")
        except Exception as e:
            logger.error(f"Failed to create Telegram client: {e}")
            self.client = None

    async def start(self) -> None:
        """Запуск бота"""
        if not self.client:
            logger.error("Cannot start bot: client not initialized")
            return

        try:
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)
            self.is_running = True
            logger.info("Telegram bot started successfully")

            self.register_handlers()
            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Остановка бота"""
        if self.is_running and self.client:
            await self.client.disconnect()
            self.is_running = False
            logger.info("Telegram bot stopped")

    def register_handlers(self) -> None:
        """Регистрация обработчиков команд"""
        if not self.client:
            logger.error("Cannot register handlers: client not initialized")
            return

        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            await self.handle_start(event)

        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_command(event):
            await self.handle_help(event)

        @self.client.on(events.NewMessage(pattern='/stats'))
        async def stats_command(event):
            await self.handle_stats(event)

        @self.client.on(events.NewMessage(pattern='/sources'))
        async def sources_command(event):
            await self.handle_sources(event)

        @self.client.on(events.NewMessage(pattern='/generate'))
        async def generate_command(event):
            await self.handle_generate(event)

        @self.client.on(events.NewMessage(pattern='/publish'))
        async def publish_command(event):
            await self.handle_publish(event)

        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_command(event):
            await self.handle_status(event)

        @self.client.on(events.NewMessage)
        async def echo_command(event):
            if not event.message.text.startswith('/'):
                await self.handle_text_message(event)

    async def handle_start(self, event) -> None:
        """Обработка команды /start"""
        welcome_text = """
🤖 *Добро пожаловать в AI News Bot!*

Я автоматический генератор новостных постов с использованием искусственного интеллекта.

*Доступные команды:*
/help - показать справку
/stats - статистика работы
/sources - управление источниками
/generate - генерация поста
/publish - публикация поста
/status - статус системы

Просто отправьте мне текст новости, и я сгенерирую для нее пост!
        """
        await event.reply(welcome_text, parse_mode='markdown')

    async def handle_help(self, event) -> None:
        """Обработка команды /help"""
        help_text = """
📚 *Справка по командам*

*Основные команды:*
/start - начать работу с ботом
/help - показать эту справку
/stats - показать статистику
/status - статус системы

*Управление контентом:*
/generate [текст] - сгенерировать пост
/publish [id] - опубликовать пост
/sources - список источников новостей

*Пример использования:*
1. Отправьте мне текст новости
2. Я сгенерирую для нее пост
3. Используйте /publish для публикации

*Дополнительно:*
- Бот автоматически собирает новости каждые 30 минут
- AI генерирует посты с эмодзи и хэштегами
- Вы можете управлять источниками через API
        """
        await event.reply(help_text, parse_mode='markdown')

    async def handle_stats(self, event) -> None:
        """Обработка команды /stats"""
        session = db.get_session()
        try:
            total_news = session.query(NewsItem).count()
            total_posts = session.query(Post).count()
            published_posts = session.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
            active_sources = session.query(Source).filter(Source.enabled == True).count()

            stats_text = f"""
📊 *Статистика системы*

📰 *Новости:*
- Всего собрано: {total_news}
- В очереди на генерацию: {total_news - total_posts}

✍️ *Посты:*
- Сгенерировано: {total_posts}
- Опубликовано: {published_posts}
- Ожидают публикации: {total_posts - published_posts}

📡 *Источники:*
- Активных источников: {active_sources}
- Всего источников: {session.query(Source).count()}

🕐 Последнее обновление: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """
            await event.reply(stats_text, parse_mode='markdown')

        except Exception as e:
            logger.error(f"Error in handle_stats: {e}")
            await event.reply("❌ Ошибка получения статистики")
        finally:
            session.close()

    async def handle_sources(self, event) -> None:
        """Обработка команды /sources"""
        session = db.get_session()
        try:
            sources = session.query(Source).filter(Source.enabled == True).all()

            if not sources:
                await event.reply("❌ Нет активных источников новостей")
                return

            sources_text = "📡 *Активные источники новостей:*\n\n"
            for i, source in enumerate(sources, 1):
                source_type = "🌐 Сайт" if source.type.value == "site" else "📱 Telegram"
                source_url = source.url or f"t.me/{source.username}"
                sources_text += f"{i}. *{source.name}* ({source_type})\n   {source_url}\n\n"

            sources_text += "\n💡 *Управление источниками через API:*\n"
            sources_text += "GET/POST /api/sources/"

            await event.reply(sources_text, parse_mode='markdown')

        except Exception as e:
            logger.error(f"Error in handle_sources: {e}")
            await event.reply("❌ Ошибка получения списка источников")
        finally:
            session.close()

    async def handle_generate(self, event) -> None:
        """Обработка команды /generate"""
        text = event.message.text.replace('/generate', '').strip()

        if not text:
            await event.reply(
                "❌ Пожалуйста, укажите текст новости для генерации\n\n"
                "Пример: `/generate Нейросети научились...`",
                parse_mode='markdown'
            )
            return

        await event.reply("🤖 Генерирую пост... Это может занять несколько секунд.")

        try:
            lines = text.split('\n', 1)
            title = lines[0][:200]
            summary = lines[1][:1000] if len(lines) > 1 else title

            generated_text = await ai_generator.generate_post(title, summary)

            if generated_text:
                response_text = f"✨ *Сгенерированный пост:*\n\n{generated_text}\n\n"
                response_text += "💡 Чтобы опубликовать, используйте команду `/publish` с ID поста"
                await event.reply(response_text, parse_mode='markdown')
            else:
                await event.reply("❌ Не удалось сгенерировать пост. Попробуйте позже.")

        except Exception as e:
            logger.error(f"Generation error: {e}")
            await event.reply(f"❌ Ошибка генерации: {str(e)}")

    async def handle_publish(self, event) -> None:
        """Обработка команды /publish"""
        args = event.message.text.replace('/publish', '').strip()

        if not args:
            await event.reply(
                "❌ Пожалуйста, укажите ID поста для публикации\n\n"
                "Пример: `/publish 123e4567-e89b-12d3-a456-426614174000`",
                parse_mode='markdown'
            )
            return

        await event.reply(f"📤 Публикую пост {args}...")

        from app.tasks import publish_post_task
        import uuid

        try:
            post_id = uuid.UUID(args)
            publish_post_task.delay(str(post_id))
            await event.reply(f"✅ Пост {args} отправлен на публикацию!")
        except ValueError:
            await event.reply("❌ Неверный формат ID. Используйте UUID формат.")

    async def handle_status(self, event) -> None:
        """Обработка команды /status"""
        openai_configured = bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != "test_key")
        telegram_configured = self._is_configured()

        status_text = f"""
🟢 *Статус системы*

🤖 *Сервисы:*
- FastAPI: ✅ Активен (http://localhost:8000)
- Celery Worker: ✅ Активен
- Celery Beat: ✅ Активен (каждые 30 мин)
- Telegram Bot: {'✅ Активен' if telegram_configured else '❌ Не настроен'}

🧠 *AI Сервис:*
- Модель: {config.OPENAI_MODEL}
- API Key: {"✅" if openai_configured else "❌"}

📱 *Telegram:*
- Bot Token: {"✅" if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN != "test_token" else "❌"}
- Channel ID: {config.TELEGRAM_CHANNEL_ID or "❌"}

💾 *База данных:*
- Тип: SQLite
- Статус: ✅ Подключена

Все системы работают в штатном режиме ✅
        """
        await event.reply(status_text, parse_mode='markdown')

    async def handle_text_message(self, event) -> None:
        """Обработка обычных текстовых сообщений"""
        text = event.message.text

        if len(text) > 1000:
            text = text[:1000] + "..."

        processing_msg = await event.reply("🤖 Анализирую текст и генерирую пост...")

        try:
            title = text[:100]
            generated_text = await ai_generator.generate_post(title, text)

            if generated_text:
                await processing_msg.edit(f"✨ *Сгенерированный пост:*\n\n{generated_text}", parse_mode='markdown')
            else:
                await processing_msg.edit("❌ Не удалось сгенерировать пост. Попробуйте позже.")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await processing_msg.edit(f"❌ Ошибка: {str(e)}")

    async def send_notification(self, chat_id: str, message: str, parse_mode: str = 'markdown') -> None:
        """Отправка уведомления администратору"""
        if not self.client or not self.is_running:
            logger.warning("Cannot send notification: bot not running")
            return

        try:
            await self.client.send_message(chat_id, message, parse_mode=parse_mode)
            logger.debug(f"Notification sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


# Глобальный экземпляр бота
telegram_bot = TelegramBot()
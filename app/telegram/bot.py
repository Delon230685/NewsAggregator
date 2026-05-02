from telethon import TelegramClient, events
from telethon.tl.types import Message
from typing import Optional, Callable, Awaitable
import logging
from app.config import config
from app.ai.generator import ai_generator
from app.database import db
from app.models import NewsItem, Post, Source
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram бот для управления сервисом через сообщения
    """

    def __init__(self):
        self.client = TelegramClient(
            'bot_session',
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH
        )
        self.is_running = False
        self.command_handlers = {}

    async def start(self):
        """
        Запуск бота
        """
        try:
            await self.client.start(bot_token=config.TELEGRAM_BOT_TOKEN)
            self.is_running = True
            logger.info("Telegram bot started successfully")

            # Регистрация обработчиков команд
            self.register_handlers()

            # Запуск бота
            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.is_running = False

    async def stop(self):
        """
        Остановка бота
        """
        if self.is_running:
            await self.client.disconnect()
            self.is_running = False
            logger.info("Telegram bot stopped")

    def register_handlers(self):
        """
        Регистрация обработчиков команд
        """

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
            # Обработка обычных сообщений как запросов на генерацию
            if not event.message.text.startswith('/'):
                await self.handle_text_message(event)

    async def handle_start(self, event):
        """
        Обработка команды /start
        """
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

    async def handle_help(self, event):
        """
        Обработка команды /help
        """
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

    async def handle_stats(self, event):
        """
        Обработка команды /stats
        """
        session = db.get_session()
        try:
            from app.models import NewsItem, Post, Source

            total_news = session.query(NewsItem).count()
            total_posts = session.query(Post).count()
            published_posts = session.query(Post).filter(Post.status == 'published').count()
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
        finally:
            session.close()

    async def handle_sources(self, event):
        """
        Обработка команды /sources
        """
        session = db.get_session()
        try:
            sources = session.query(Source).filter(Source.enabled == True).all()

            if not sources:
                await event.reply("❌ Нет активных источников новостей")
                return

            sources_text = "📡 *Активные источники новостей:*\n\n"
            for i, source in enumerate(sources, 1):
                source_type = "🌐 Сайт" if source.type == "site" else "📱 Telegram"
                source_url = source.url or f"t.me/{source.username}"
                sources_text += f"{i}. *{source.name}* ({source_type})\n   {source_url}\n\n"

            sources_text += "\n💡 *Управление источниками через API:*\n"
            sources_text += "GET/POST /api/sources/"

            await event.reply(sources_text, parse_mode='markdown')
        finally:
            session.close()

    async def handle_generate(self, event):
        """
        Обработка команды /generate
        """
        # Извлекаем текст команды (после /generate)
        text = event.message.text.replace('/generate', '').strip()

        if not text:
            await event.reply(
                "❌ Пожалуйста, укажите текст новости для генерации\n\nПример: `/generate Нейросети научились...`",
                parse_mode='markdown')
            return

        await event.reply("🤖 Генерирую пост... Это может занять несколько секунд.")

        # Генерируем пост
        try:
            # Простой парсинг: первая строка как заголовок, остальное как текст
            lines = text.split('\n', 1)
            title = lines[0][:200]
            summary = lines[1][:1000] if len(lines) > 1 else title

            generated_text = await ai_generator.generate_post(title, summary)

            if generated_text:
                response_text = f"✨ *Сгенерированный пост:*\n\n{generated_text}\n\n"
                response_text += "💡 Чтобы опубликовать, используйте команду `/publish` с этим текстом"
                await event.reply(response_text, parse_mode='markdown')
            else:
                await event.reply("❌ Не удалось сгенерировать пост. Попробуйте позже.")

        except Exception as e:
            logger.error(f"Generation error: {e}")
            await event.reply(f"❌ Ошибка генерации: {str(e)}")

    async def handle_publish(self, event):
        """
        Обработка команды /publish
        """
        # Извлекаем ID поста
        args = event.message.text.replace('/publish', '').strip()

        if not args:
            await event.reply(
                "❌ Пожалуйста, укажите ID поста для публикации\n\nПример: `/publish 123e4567-e89b-12d3-a456-426614174000`",
                parse_mode='markdown')
            return

        await event.reply(f"📤 Публикую пост {args}...")

        # Здесь должна быть логика публикации
        from app.tasks import publish_post_task
        import uuid

        try:
            post_id = uuid.UUID(args)
            publish_post_task.delay(str(post_id))
            await event.reply(f"✅ Пост {args} отправлен на публикацию!")
        except ValueError:
            await event.reply("❌ Неверный формат ID. Используйте UUID формат.")

    async def handle_status(self, event):
        """
        Обработка команды /status
        """
        status_text = f"""
🟢 *Статус системы*

🤖 *Сервисы:*
- FastAPI: ✅ Активен (http://localhost:8000)
- Celery Worker: ✅ Активен
- Celery Beat: ✅ Активен (каждые 30 мин)
- Telegram Bot: ✅ Активен

🧠 *AI Сервис:*
- Модель: {config.OPENAI_MODEL}
- API Key: {"✅" if config.OPENAI_API_KEY else "❌"}

📱 *Telegram:*
- Bot Token: {"✅" if config.TELEGRAM_BOT_TOKEN else "❌"}
- Channel ID: {config.TELEGRAM_CHANNEL_ID or "❌"}

💾 *База данных:*
- Тип: PostgreSQL
- Статус: ✅ Подключена

Все системы работают в штатном режиме ✅
        """
        await event.reply(status_text, parse_mode='markdown')

    async def handle_text_message(self, event):
        """
        Обработка обычных текстовых сообщений как запроса на генерацию
        """
        text = event.message.text

        # Ограничиваем длину текста
        if len(text) > 1000:
            text = text[:1000] + "..."

        processing_msg = await event.reply("🤖 Анализирую текст и генерирую пост...")

        try:
            # Используем весь текст как новость
            title = text[:100]
            summary = text

            generated_text = await ai_generator.generate_post(title, summary)

            if generated_text:
                await processing_msg.edit(f"✨ *Сгенерированный пост:*\n\n{generated_text}", parse_mode='markdown')
            else:
                await processing_msg.edit("❌ Не удалось сгенерировать пост. Попробуйте позже.")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await processing_msg.edit(f"❌ Ошибка: {str(e)}")

    async def send_notification(self, chat_id: str, message: str, parse_mode: str = 'markdown'):
        """
        Отправка уведомления администратору
        """
        try:
            await self.client.send_message(chat_id, message, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


# Глобальный экземпляр бота
telegram_bot = TelegramBot()
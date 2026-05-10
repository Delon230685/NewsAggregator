"""OpenAI клиент для генерации постов"""

from openai import AsyncOpenAI
from typing import Optional
import time

from app.config import config
from app.logger import logger


class OpenAIClient:
    """Клиент для работы с OpenAI API"""

    def __init__(self) -> None:
        """Инициализация OpenAI клиента"""
        api_key = config.OPENAI_API_KEY
        self.default_model = config.OPENAI_MODEL

        # Проверка наличия API ключа
        if not api_key or api_key == "test_key":
            logger.warning("OpenAI API key not set or using test key. AI generation will fail.")
        else:
            logger.info(f"OpenAI client initialized with model: {self.default_model}")
            logger.debug(f"API key: {api_key[:20]}...")

        self.client = AsyncOpenAI(api_key=api_key)
        self.request_count = 0
        self.total_tokens = 0

    async def generate_post(
            self,
            title: str,
            content: str,
            style: str = "casual",
            include_emoji: bool = True,
            include_hashtags: bool = True,
            max_length: int = 500
    ) -> Optional[str]:
        """
        Генерация поста для Telegram через OpenAI

        Args:
            title: Заголовок новости
            content: Текст новости
            style: Стиль поста (casual, news, professional)
            include_emoji: Добавлять ли эмодзи
            include_hashtags: Добавлять ли хэштеги
            max_length: Максимальная длина поста

        Returns:
            Сгенерированный текст поста или None при ошибке
        """

        # Настройка инструкций в зависимости от стиля
        style_instructions = {
            "casual": "Сделай пост в дружеском, развлекательном стиле",
            "news": "Сделай пост в информационном, новостном стиле",
            "professional": "Сделай пост в деловом, профессиональном стиле"
        }
        style_instruction = style_instructions.get(style, style_instructions["casual"])

        emoji_instruction = "Добавь 2-3 подходящих эмодзи" if include_emoji else "Не используй эмодзи"
        hashtag_instruction = "Добавь 2-3 релевантных хэштега в конце" if include_hashtags else "Не добавляй хэштеги"

        prompt = f"""
{style_instruction}

Создай пост на основе этой новости:
Заголовок: {title}
Текст: {content}

Требования:
- Максимум {max_length} символов
- {emoji_instruction}
- {hashtag_instruction}
- Сделай пост ярким, вовлекающим
- Добавь краткий вывод или вопрос для подписчиков

Ответь только текстом поста, без пояснений.
"""

        try:
            start_time = time.time()
            logger.info(f"Sending request to OpenAI for: {title[:50]}...")

            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system",
                     "content": "Ты - профессиональный копирайтер для Telegram канала. Отвечаешь только текстом поста, без пояснений и кавычек."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )

            # Обновляем статистику
            self.request_count += 1
            if response.usage:
                self.total_tokens += response.usage.total_tokens

            generated_text = response.choices[0].message.content
            elapsed_time = (time.time() - start_time) * 1000

            logger.info(
                f"OpenAI response received - "
                f"Model: {self.default_model}, "
                f"Tokens: {response.usage.total_tokens if response.usage else 'N/A'}, "
                f"Time: {elapsed_time:.0f}ms"
            )

            return generated_text

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def get_stats(self) -> dict[str, int]:
        """
        Получить статистику использования OpenAI API

        Returns:
            Словарь со статистикой
        """
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "model": self.default_model
        }

    def estimate_cost(self) -> float:

        if "gpt-4" in self.default_model:
            cost_per_1k = 0.03
        else:
            cost_per_1k = 0.002

        return (self.total_tokens / 1000) * cost_per_1k

    def reset_stats(self) -> None:
        """Сброс статистики использования"""
        self.request_count = 0
        self.total_tokens = 0
        logger.info("OpenAI client statistics reset")


openai_client = OpenAIClient()
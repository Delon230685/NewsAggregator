"""AI генератор постов для Telegram"""

from typing import Optional
import random

from app.ai.openai_client import openai_client
from app.logger import logger


class AIGenerator:
    """Генератор постов с использованием AI"""

    def __init__(self) -> None:
        """Инициализация генератора"""
        self.client = openai_client
        logger.debug("AIGenerator initialized")

    async def generate_post(
            self,
            title: str,
            summary: str,
            style: str = "casual"
    ) -> Optional[str]:
        """
        Генерация поста через OpenAI

        Args:
            title: Заголовок новости
            summary: Краткое содержание новости
            style: Стиль поста (casual, news, professional)

        Returns:
            Сгенерированный текст поста или None при ошибке
        """
        try:
            logger.info(f"Generating post with AI for: {title[:50]}...")

            # Пробуем реальную генерацию через OpenAI
            generated_text = await self.client.generate_post(
                title=title,
                content=summary,
                style=style,
                include_emoji=True,
                include_hashtags=True,
                max_length=500
            )

            if generated_text:
                logger.info(f"Successfully generated post for: {title[:50]}...")
                return generated_text
            else:
                logger.warning(f"OpenAI returned empty response, using fallback for: {title[:50]}...")
                return self._fallback_generation(title, summary)

        except Exception as e:
            logger.error(f"Error generating post with AI: {e}")
            return self._fallback_generation(title, summary)

    def _fallback_generation(self, title: str, summary: str) -> str:
        """
        Fallback генерация (если API недоступен)

        Args:
            title: Заголовок новости
            summary: Краткое содержание новости

        Returns:
            Сгенерированный текст поста
        """
        logger.debug(f"Using fallback generation for: {title[:50]}...")

        emojis = ["🔥", "💡", "📰", "🤯", "⚡️", "🎯", "💎", "🌟", "⭐", "💪"]
        cta_variants = [
            "✨ Присоединяйтесь к нашему Telegram-каналу!",
            "👉 Подпишитесь, чтобы узнавать первыми!",
            "💬 Напишите своё мнение в комментариях!",
            "🔄 Поделитесь с друзьями, если было интересно!",
            "⭐ Поставьте лайк, если поддерживаете!"
        ]
        hashtags_variants = [
            "#новости #актуально",
            "#главное #сегодня",
            "#важно #интересно",
            "#свежиеновости #топ"
        ]

        post_text = f"""
{random.choice(emojis)} {title}

{summary[:300]}{'...' if len(summary) > 300 else ''}

{random.choice(cta_variants)}

{random.choice(hashtags_variants)}
        """.strip()

        logger.debug(f"Fallback post generated, length: {len(post_text)} chars")
        return post_text


# Глобальный экземпляр генератора
ai_generator = AIGenerator()
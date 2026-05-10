from app.ai.openai_client import openai_client
from typing import Optional
import logging
import random

logger = logging.getLogger(__name__)


class AIGenerator:
    def __init__(self):
        self.client = openai_client

    async def generate_post(self, title: str, summary: str, style: str = "casual") -> Optional[str]:
        """Генерация поста через OpenAI"""
        try:
            # Пробуем реальную генерацию
            generated_text = await self.client.generate_post(
                title=title,
                content=summary,
                style=style,
                include_emoji=True,
                include_hashtags=True,
                max_length=500
            )

            if generated_text:
                logger.info(f"AI generated post for: {title[:50]}")
                return generated_text
            else:
                return self._fallback_generation(title, summary)

        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return self._fallback_generation(title, summary)

    def _fallback_generation(self, title: str, summary: str) -> str:
        """Fallback если API недоступен"""
        emojis = ["🔥", "💡", "📰", "🤯", "⚡️", "🎯", "💎", "🌟"]
        cta_variants = [
            "✨ Присоединяйтесь к нашему Telegram-каналу!",
            "👉 Подпишитесь, чтобы узнавать первыми!",
            "💬 Напишите своё мнение в комментариях!"
        ]

        return f"""
{random.choice(emojis)} {title}

{summary[:300]}...

{random.choice(cta_variants)}

#новости #актуально
        """.strip()


ai_generator = AIGenerator()
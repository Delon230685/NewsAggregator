from app.ai.openai_client import openai_client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AIGenerator:
    def __init__(self):
        self.client = openai_client

    async def generate_post(self, title: str, summary: str, style: str = "casual") -> Optional[str]:
        """
        Генерация поста для Telegram с использованием OpenAI клиента
        """
        try:
            # Временно используем fallback для тестов
            # Если нет API ключа, используем генерацию без AI
            if not self.client.client.api_key or self.client.client.api_key == "test_key":
                return self._fallback_generation(title, summary)

            generated_text = await self.client.generate_post(
                title=title,
                content=summary,
                style=style,
                include_emoji=True,
                include_hashtags=True,
                max_length=500
            )

            if generated_text:
                return generated_text
            else:
                return self._fallback_generation(title, summary)

        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return self._fallback_generation(title, summary)

    def _fallback_generation(self, title: str, summary: str) -> str:
        """Fallback генерация без AI"""
        import random

        emojis = ["🔥", "💡", "📰", "🤯", "⚡️", "🎯", "💎", "🌟"]
        emoji = random.choice(emojis)

        # Берем первое предложение
        first_sentence = summary.split('.')[0] if summary else ""

        return f"""
{emoji} *{title}*

{first_sentence}{'...' if len(first_sentence) < len(summary) else ''}

👉 Узнайте больше по ссылке

#новости #актуально #{title.split()[0] if title else 'новость'}
        """.strip()


ai_generator = AIGenerator()
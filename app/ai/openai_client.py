from openai import AsyncOpenAI
from app.config import config
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.default_model = config.OPENAI_MODEL

    async def generate_post(self, title: str, content: str, style: str = "casual",
                            include_emoji: bool = True, include_hashtags: bool = True,
                            max_length: int = 500) -> str:
        """Генерация поста для Telegram через OpenAI"""

        emoji_instruction = "Добавь 2-3 подходящих эмодзи" if include_emoji else "Не используй эмодзи"
        hashtag_instruction = "Добавь 2-3 релевантных хэштега в конце" if include_hashtags else "Не добавляй хэштеги"

        prompt = f"""
Ты - профессиональный копирайтер для Telegram-канала.

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
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system",
                     "content": "Ты - профессиональный копирайтер для Telegram. Отвечаешь только текстом поста."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )

            generated_text = response.choices[0].message.content
            logger.info(f"Generated post with {self.default_model}")
            return generated_text

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


openai_client = OpenAIClient()
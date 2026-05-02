import openai
from openai import AsyncOpenAI, OpenAI
from typing import Optional, Dict, Any, List, Tuple
import logging
import time
from datetime import datetime
from app.config import config
from app.utils import RateLimiter, retry_on_failure
from app.database import db
from app.models import GenerationLog

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Клиент для работы с OpenAI API с расширенным функционалом
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.sync_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.default_model = config.OPENAI_MODEL
        self.rate_limiter = RateLimiter(max_calls=60, time_window=60)  # 60 запросов в минуту

    @retry_on_failure(max_retries=3, delay=2, backoff=2)
    async def generate_text(self,
                            prompt: str,
                            system_message: str = "You are a helpful assistant.",
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: int = 500,
                            log_generation: bool = True) -> Optional[Tuple[str, Dict]]:
        """
        Генерация текста с помощью OpenAI API

        Args:
            prompt: Пользовательский промпт
            system_message: Системное сообщение
            model: Модель (если не указана, используется default)
            temperature: Температура генерации (0-1)
            max_tokens: Максимальное количество токенов
            log_generation: Логировать ли генерацию

        Returns:
            Tuple[str, Dict] - (сгенерированный текст, метаданные) или None
        """

        # Проверяем rate limit
        if not self.rate_limiter.can_call():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(f"Rate limit reached, waiting {wait_time} seconds")
            time.sleep(wait_time)

        model = model or self.default_model
        start_time = time.time()

        try:
            # Вызов API
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1
            )

            generation_time = int((time.time() - start_time) * 1000)
            generated_text = response.choices[0].message.content

            # Получаем информацию о токенах
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            # Рассчитываем стоимость (грубо: $0.03 за 1K токенов для GPT-4)
            cost_per_1k = 0.03 if "gpt-4" in model else 0.002
            cost_usd = int((total_tokens / 1000) * cost_per_1k * 1_000_000)

            metadata = {
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost_usd,
                'generation_time': generation_time,
                'temperature': temperature,
                'max_tokens': max_tokens
            }

            # Логируем генерацию
            if log_generation:
                await self.log_generation(
                    prompt=prompt,
                    generated_text=generated_text,
                    success=True,
                    metadata=metadata
                )

            logger.info(f"Generated text with {model}: {total_tokens} tokens, {generation_time}ms")
            return generated_text, metadata

        except Exception as e:
            logger.error(f"Error generating text: {e}")

            # Логируем ошибку
            if log_generation:
                await self.log_generation(
                    prompt=prompt,
                    generated_text=None,
                    success=False,
                    error_message=str(e)
                )

            return None, None

    async def generate_post(self,
                            title: str,
                            content: str,
                            style: str = "news",
                            include_emoji: bool = True,
                            include_hashtags: bool = True,
                            max_length: int = 500) -> Optional[str]:
        """
        Генерация поста для Telegram

        Args:
            title: Заголовок новости
            content: Содержание новости
            style: Стиль поста (news, casual, professional)
            include_emoji: Добавлять ли эмодзи
            include_hashtags: Добавлять ли хэштеги
            max_length: Максимальная длина поста
        """

        # Настройка промпта в зависимости от стиля
        style_prompts = {
            "news": "Сделай информативный новостной пост в серьезном стиле",
            "casual": "Сделай легкий, развлекательный пост в дружеском стиле",
            "professional": "Сделай профессиональный деловой пост"
        }

        style_desc = style_prompts.get(style, style_prompts["news"])

        emoji_instruction = "Добавь 2-3 подходящих эмодзи в начале или в тексте" if include_emoji else "Не используй эмодзи"
        hashtag_instruction = "Добавь 2-3 релевантных хэштега в конце" if include_hashtags else "Не добавляй хэштеги"

        prompt = f"""
Используя новость ниже, создай пост для Telegram-канала.

Заголовок: {title}
Содержание: {content}

Требования к посту:
1. {style_desc}
2. {emoji_instruction}
3. {hashtag_instruction}
4. Максимальная длина: {max_length} символов
5. Пост должен быть интересным и вовлекающим
6. Добавь краткий вывод или вопрос для подписчиков

Ответь только текстом поста без дополнительных комментариев.
        """

        system_message = "Ты - профессиональный копирайтер для Telegram-каналов. Твои посты всегда привлекают внимание и вовлекают аудиторию."

        result, metadata = await self.generate_text(
            prompt=prompt,
            system_message=system_message,
            temperature=0.7,
            max_tokens=max_length
        )

        return result

    async def summarize_news(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        Суммаризация новости
        """
        prompt = f"""
Сделай краткую суммуризацию следующей новости.
Сохрани ключевые факты, но убери лишние детали.
Максимальная длина: {max_length} символов.

Новость: {text}

Суммаризация:
        """

        system_message = "Ты - профессиональный редактор новостей, делающий краткие и точные суммаризации."

        result, metadata = await self.generate_text(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3,
            max_tokens=max_length
        )

        return result

    async def extract_keywords(self, text: str, top_n: int = 5) -> Optional[List[str]]:
        """
        Извлечение ключевых слов из текста
        """
        prompt = f"""
Извлеки {top_n} ключевых слов из следующего текста.
Ключевые слова должны быть на русском языке, существительные в именительном падеже.
Ответь списком слов через запятую, без дополнительных комментариев.

Текст: {text}

Ключевые слова:
        """

        system_message = "Ты - специалист по обработке текстов и извлечению ключевых слов."

        result, metadata = await self.generate_text(
            prompt=prompt,
            system_message=system_message,
            temperature=0.2,
            max_tokens=100
        )

        if result:
            # Парсим результат
            keywords = [kw.strip() for kw in result.split(',')]
            return keywords[:top_n]

        return None

    async def check_relevance(self,
                              news_text: str,
                              keywords: List[str]) -> Tuple[bool, int]:
        """
        Проверка релевантности новости на основе ключевых слов
        """
        prompt = f"""
Оцени релевантность следующей новости на основе заданных ключевых слов.
Оценка должна быть от 0 до 100, где 100 - максимально релевантно.

Ключевые слова: {', '.join(keywords)}

Новость: {news_text}

Ответь в формате: ОЦЕНКА: [число]
        """

        result, metadata = await self.generate_text(
            prompt=prompt,
            system_message="Ты - специалист по оценке релевантности контента.",
            temperature=0.1,
            max_tokens=50
        )

        try:
            if result:
                score_line = [line for line in result.split('\n') if 'ОЦЕНКА' in line]
                if score_line:
                    score = int(''.join(filter(str.isdigit, score_line[0])))
                    score = max(0, min(100, score))
                    relevance = score >= 50
                    return relevance, score
        except:
            pass

        return False, 0

    async def rewrite_post(self, post_text: str, style: str = "improve") -> Optional[str]:
        """
        Переписывание поста в другом стиле
        """
        style_instructions = {
            "improve": "Улучши пост: сделай его более привлекательным и интересным",
            "shorter": "Сделай пост короче, сохранив основную суть",
            "longer": "Расширь пост, добавив больше деталей и контекста",
            "formal": "Перепиши пост в более формальном стиле",
            "casual": "Перепиши пост в более неформальном, дружеском стиле"
        }

        instruction = style_instructions.get(style, style_instructions["improve"])

        prompt = f"""
Исходный пост: {post_text}

{instruction}

Важно: Сохрани ключевое сообщение и призыв к действию.
        """

        result, metadata = await self.generate_text(
            prompt=prompt,
            system_message="Ты - профессиональный копирайтер и редактор текстов.",
            temperature=0.6,
            max_tokens=600
        )

        return result

    async def log_generation(self,
                             prompt: str,
                             generated_text: Optional[str],
                             success: bool,
                             metadata: Optional[Dict] = None,
                             error_message: Optional[str] = None,
                             news_id: Optional[str] = None,
                             post_id: Optional[str] = None):
        """
        Логирование генерации в БД
        """
        session = db.get_session()
        try:
            log = GenerationLog(
                news_id=news_id,
                post_id=post_id,
                model_used=metadata.get('model') if metadata else None,
                prompt_tokens=metadata.get('prompt_tokens') if metadata else None,
                completion_tokens=metadata.get('completion_tokens') if metadata else None,
                total_tokens=metadata.get('total_tokens') if metadata else None,
                cost_usd=metadata.get('cost_usd') if metadata else None,
                generation_time=metadata.get('generation_time') if metadata else None,
                success=success,
                error_message=error_message
            )
            session.add(log)
            session.commit()
        except Exception as e:
            logger.error(f"Error logging generation: {e}")
        finally:
            session.close()

    def get_cached_response(self, prompt: str) -> Optional[str]:
        """
        Получение кэшированного ответа (для уменьшения затрат)
        """
        # Здесь можно реализовать кэширование в Redis
        return None

    def estimate_cost(self, text_length: int, model: Optional[str] = None) -> float:
        """
        Оценка стоимости генерации
        """
        model = model or self.default_model
        tokens_estimate = text_length // 4  # Приблизительно

        # Цены за 1K токенов
        pricing = {
            "gpt-4": 0.03,
            "gpt-4-1106-preview": 0.01,
            "gpt-3.5-turbo": 0.002
        }

        price_per_1k = pricing.get(model, 0.002)
        estimated_cost = (tokens_estimate / 1000) * price_per_1k

        return estimated_cost


# Глобальный экземпляр
openai_client = OpenAIClient()
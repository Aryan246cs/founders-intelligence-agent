from groq import Groq
from config import settings
from utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_client: Groq | None = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def complete(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    client = get_groq_client()
    model = model or settings.groq_model

    logger.debug("Groq completion request", model=model)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content
    logger.debug("Groq completion received", tokens=response.usage.total_tokens)
    return content

from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import AIResponse, BaseAIProvider
from app.core.exceptions import AIProviderError, AIProviderNotConfigured
from app.core.logging import get_logger

log = get_logger(__name__)


class OpenAIProvider(BaseAIProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise AIProviderNotConfigured(
                "OPENAI_API_KEY is not set.", provider="openai"
            )
        self._model = model
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=api_key)
        except ImportError as exc:
            raise AIProviderNotConfigured(
                "openai package is not installed. Run: pip install openai"
            ) from exc

    @property
    def model_name(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def complete(self, prompt: str, system: str = "") -> AIResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.3,
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage
            log.debug(
                "openai_completion",
                model=self._model,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )
            return AIResponse(
                content=content,
                model=self._model,
                provider="openai",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )
        except Exception as exc:
            raise AIProviderError(
                f"OpenAI completion failed: {exc}", provider="openai"
            ) from exc

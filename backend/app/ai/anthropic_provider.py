from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import AIResponse, BaseAIProvider
from app.core.exceptions import AIProviderError, AIProviderNotConfigured
from app.core.logging import get_logger

log = get_logger(__name__)


class AnthropicProvider(BaseAIProvider):
    provider_name = "anthropic"

    def __init__(
        self, api_key: str, model: str = "claude-haiku-4-5-20251001"
    ) -> None:
        if not api_key:
            raise AIProviderNotConfigured(
                "ANTHROPIC_API_KEY is not set.", provider="anthropic"
            )
        self._model = model
        try:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError as exc:
            raise AIProviderNotConfigured(
                "anthropic package is not installed. Run: pip install anthropic"
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
        try:
            import anthropic

            kwargs: dict = {
                "model": self._model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            response = await self._client.messages.create(**kwargs)
            content = response.content[0].text if response.content else ""
            log.debug(
                "anthropic_completion",
                model=self._model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            return AIResponse(
                content=content,
                model=self._model,
                provider="anthropic",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
        except Exception as exc:
            raise AIProviderError(
                f"Anthropic completion failed: {exc}", provider="anthropic"
            ) from exc

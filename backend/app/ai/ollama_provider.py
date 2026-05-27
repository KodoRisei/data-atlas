import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import AIResponse, BaseAIProvider
from app.core.exceptions import AIProviderError
from app.core.logging import get_logger

log = get_logger(__name__)


class OllamaProvider(BaseAIProvider):
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def model_name(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def complete(self, prompt: str, system: str = "") -> AIResponse:
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        }
        if system:
            payload["system"] = system

        try:
            response = await self._client.post(
                f"{self._base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "")
            log.debug(
                "ollama_completion",
                model=self._model,
                eval_count=data.get("eval_count", 0),
            )
            return AIResponse(
                content=content,
                model=self._model,
                provider="ollama",
                output_tokens=data.get("eval_count", 0),
            )
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                f"Ollama request failed: {exc.response.status_code} {exc.response.text}",
                provider="ollama",
            ) from exc
        except Exception as exc:
            raise AIProviderError(
                f"Ollama completion failed: {exc}", provider="ollama"
            ) from exc

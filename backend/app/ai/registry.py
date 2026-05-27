from functools import lru_cache

from app.ai.base import BaseAIProvider
from app.core.config import get_settings
from app.core.exceptions import AIProviderNotConfigured


@lru_cache
def get_ai_provider() -> BaseAIProvider:
    """
    Returns the configured AI provider singleton.
    Called lazily so startup doesn't fail if no API key is configured.
    """
    settings = get_settings()
    provider = settings.ai_provider

    if provider == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    if provider == "anthropic":
        from app.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    if provider == "ollama":
        from app.ai.ollama_provider import OllamaProvider

        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    raise AIProviderNotConfigured(
        f"Unknown AI provider '{provider}'. Choose: openai | anthropic | ollama"
    )

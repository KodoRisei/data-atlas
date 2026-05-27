from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseAIProvider(ABC):
    """Abstract AI provider. Swap implementations without changing service code."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier: openai | anthropic | ollama"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The specific model being used."""

    @abstractmethod
    async def complete(self, prompt: str, system: str = "") -> AIResponse:
        """
        Send a prompt and return a completion.
        Implementations must handle retries and error wrapping internally.
        """

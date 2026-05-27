from typing import Any


class DataAtlasError(Exception):
    """Base exception for all DataAtlas domain errors."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context


class NotFoundError(DataAtlasError):
    """Resource not found."""


class ConflictError(DataAtlasError):
    """Resource already exists."""


class IngestionError(DataAtlasError):
    """Failed to ingest metadata from a source database."""


class LineageParseError(DataAtlasError):
    """Failed to parse SQL for lineage extraction."""


class AIProviderError(DataAtlasError):
    """AI provider call failed."""


class AIProviderNotConfigured(DataAtlasError):
    """AI provider credentials are missing."""


class UnsupportedConnectorError(DataAtlasError):
    """Database type is not supported."""


class ValidationError(DataAtlasError):
    """Input validation failed."""

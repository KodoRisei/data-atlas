from app.core.exceptions import UnsupportedConnectorError
from app.ingestion.base import BaseConnector
from app.ingestion.postgresql import PostgreSQLConnector


def get_connector(db_url: str) -> BaseConnector:
    """Factory: returns the right connector for the given database URL."""
    scheme = db_url.split("://")[0].split("+")[0].lower()

    if scheme in {"postgresql", "postgres"}:
        # Strip asyncpg/psycopg2 driver prefix for the target scan connection
        clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        clean_url = clean_url.replace("postgresql+psycopg2://", "postgresql://")
        return PostgreSQLConnector(dsn=clean_url)

    raise UnsupportedConnectorError(
        f"No connector available for database scheme '{scheme}'.",
        scheme=scheme,
    )

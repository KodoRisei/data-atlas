from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawColumnInfo:
    column_name: str
    ordinal_position: int
    data_type: str
    is_nullable: bool
    default_value: str | None = None
    character_maximum_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None


@dataclass
class RawTableInfo:
    schema_name: str
    table_name: str
    table_type: str  # table | view | materialized_view
    row_count: int | None = None
    size_bytes: int | None = None
    owner: str | None = None
    view_definition: str | None = None
    columns: list[RawColumnInfo] = field(default_factory=list)


@dataclass
class IngestionResult:
    source_name: str
    tables: list[RawTableInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseConnector(ABC):
    """Abstract connector for scanning a source database schema."""

    @property
    @abstractmethod
    def connector_type(self) -> str:
        """Identifies the database engine (e.g. 'postgresql')."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the source database."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close and clean up the connection."""

    @abstractmethod
    async def scan(
        self,
        schemas: list[str] | None = None,
        exclude_schemas: list[str] | None = None,
    ) -> IngestionResult:
        """Scan the source database and return raw metadata."""

    async def __aenter__(self) -> "BaseConnector":
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

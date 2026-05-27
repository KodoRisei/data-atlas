import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import IngestionError
from app.core.logging import get_logger
from app.ingestion.base import (
    BaseConnector,
    IngestionResult,
    RawColumnInfo,
    RawTableInfo,
)

log = get_logger(__name__)

_EXCLUDED_SCHEMAS = frozenset(
    {"pg_catalog", "pg_toast", "information_schema", "pg_temp"}
)

_TABLE_TYPE_MAP = {
    "BASE TABLE": "table",
    "VIEW": "view",
}


class PostgreSQLConnector(BaseConnector):
    """Scans a PostgreSQL database via information_schema and system catalogs."""

    connector_type = "postgresql"

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: asyncpg.Connection | None = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def connect(self) -> None:
        try:
            self._conn = await asyncpg.connect(dsn=self._dsn)
            log.info("postgresql_connected", dsn=self._dsn.split("@")[-1])
        except Exception as exc:
            raise IngestionError(
                f"Cannot connect to PostgreSQL: {exc}", dsn=self._dsn
            ) from exc

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def scan(
        self,
        schemas: list[str] | None = None,
        exclude_schemas: list[str] | None = None,
    ) -> IngestionResult:
        if not self._conn:
            raise IngestionError("Not connected. Call connect() first.")

        excluded = _EXCLUDED_SCHEMAS | set(exclude_schemas or [])
        result = IngestionResult(source_name=self._dsn.split("@")[-1])

        try:
            schema_list = await self._get_schemas(schemas, excluded)
            log.info("postgresql_scanning_schemas", count=len(schema_list))

            for schema in schema_list:
                tables = await self._scan_schema(schema)
                result.tables.extend(tables)

            log.info(
                "postgresql_scan_complete",
                tables=len(result.tables),
                errors=len(result.errors),
            )
        except Exception as exc:
            result.errors.append(str(exc))
            log.error("postgresql_scan_failed", error=str(exc))

        return result

    async def _get_schemas(
        self, allow_list: list[str] | None, excluded: frozenset[str]
    ) -> list[str]:
        rows = await self._conn.fetch(  # type: ignore[union-attr]
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT LIKE 'pg_%'
              AND schema_name != 'information_schema'
            ORDER BY schema_name
            """
        )
        all_schemas = [r["schema_name"] for r in rows]
        if allow_list:
            return [s for s in all_schemas if s in allow_list and s not in excluded]
        return [s for s in all_schemas if s not in excluded]

    async def _scan_schema(self, schema: str) -> list[RawTableInfo]:
        tables: list[RawTableInfo] = []

        table_rows = await self._conn.fetch(  # type: ignore[union-attr]
            """
            SELECT
                t.table_name,
                t.table_type,
                pg_get_userbyid(c.relowner) AS owner,
                pg_total_relation_size(c.oid) AS size_bytes,
                v.view_definition
            FROM information_schema.tables t
            LEFT JOIN pg_class c
                ON c.relname = t.table_name
                AND c.relnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = $1
                )
            LEFT JOIN information_schema.views v
                ON v.table_schema = t.table_schema
                AND v.table_name = t.table_name
            WHERE t.table_schema = $1
              AND t.table_type IN ('BASE TABLE', 'VIEW')
            ORDER BY t.table_name
            """,
            schema,
        )

        # Fetch materialized views separately
        mv_rows = await self._conn.fetch(  # type: ignore[union-attr]
            """
            SELECT
                m.matviewname AS table_name,
                pg_get_userbyid(c.relowner) AS owner,
                pg_total_relation_size(c.oid) AS size_bytes,
                m.definition AS view_definition
            FROM pg_matviews m
            JOIN pg_class c ON c.relname = m.matviewname
                AND c.relnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = $1
                )
            WHERE m.schemaname = $1
            """,
            schema,
        )

        raw_tables = [
            {
                "table_name": r["table_name"],
                "table_type": _TABLE_TYPE_MAP.get(r["table_type"], "table"),
                "owner": r["owner"],
                "size_bytes": r["size_bytes"],
                "view_definition": r["view_definition"],
            }
            for r in table_rows
        ] + [
            {
                "table_name": r["table_name"],
                "table_type": "materialized_view",
                "owner": r["owner"],
                "size_bytes": r["size_bytes"],
                "view_definition": r["view_definition"],
            }
            for r in mv_rows
        ]

        for raw in raw_tables:
            try:
                row_count = await self._get_row_count(schema, raw["table_name"])
                columns = await self._get_columns(schema, raw["table_name"])

                tables.append(
                    RawTableInfo(
                        schema_name=schema,
                        table_name=raw["table_name"],
                        table_type=raw["table_type"],
                        row_count=row_count,
                        size_bytes=raw["size_bytes"],
                        owner=raw["owner"],
                        view_definition=raw["view_definition"],
                        columns=columns,
                    )
                )
            except Exception as exc:
                log.warning(
                    "postgresql_table_scan_failed",
                    schema=schema,
                    table=raw["table_name"],
                    error=str(exc),
                )

        return tables

    async def _get_row_count(self, schema: str, table: str) -> int | None:
        try:
            # Fast approximate count from pg_class statistics
            row = await self._conn.fetchrow(  # type: ignore[union-attr]
                """
                SELECT reltuples::bigint AS row_count
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = $1 AND c.relname = $2
                """,
                schema,
                table,
            )
            return row["row_count"] if row and row["row_count"] >= 0 else None
        except Exception:
            return None

    async def _get_columns(self, schema: str, table: str) -> list[RawColumnInfo]:
        rows = await self._conn.fetch(  # type: ignore[union-attr]
            """
            SELECT
                column_name,
                ordinal_position,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema,
            table,
        )
        return [
            RawColumnInfo(
                column_name=r["column_name"],
                ordinal_position=r["ordinal_position"],
                data_type=r["data_type"],
                is_nullable=r["is_nullable"] == "YES",
                default_value=r["column_default"],
                character_maximum_length=r["character_maximum_length"],
                numeric_precision=r["numeric_precision"],
                numeric_scale=r["numeric_scale"],
            )
            for r in rows
        ]

"""
Orchestrates metadata extraction: takes raw ingestion results and persists
them into the catalog database (tables + columns).
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.ingestion.base import IngestionResult, RawColumnInfo, RawTableInfo
from app.metadata.pii_detector import detect_pii
from app.persistence.models import ColumnModel, TableModel
from app.persistence.repositories.column import ColumnRepository
from app.persistence.repositories.table import TableRepository

log = get_logger(__name__)


class MetadataExtractor:
    def __init__(self, session: AsyncSession) -> None:
        self._table_repo = TableRepository(session)
        self._column_repo = ColumnRepository(session)

    async def persist(self, result: IngestionResult) -> dict[str, int]:
        """
        Upsert tables and columns from an ingestion result.
        Returns summary counts.
        """
        tables_created = 0
        tables_updated = 0
        columns_upserted = 0

        for raw_table in result.tables:
            table_model, created = await self._upsert_table(raw_table)
            if created:
                tables_created += 1
            else:
                tables_updated += 1

            col_count = await self._upsert_columns(table_model, raw_table.columns)
            columns_upserted += col_count

            await self._table_repo.update_scan_timestamp(table_model.id)

            # Mark table PII flag if any column is PII
            pii_cols = await self._column_repo.get_pii_columns_for_table(table_model.id)
            if pii_cols and not table_model.is_pii_flagged:
                await self._table_repo.mark_pii(table_model.id)

        log.info(
            "metadata_extractor_complete",
            tables_created=tables_created,
            tables_updated=tables_updated,
            columns_upserted=columns_upserted,
        )
        return {
            "tables_created": tables_created,
            "tables_updated": tables_updated,
            "columns_upserted": columns_upserted,
        }

    async def _upsert_table(self, raw: RawTableInfo) -> tuple[TableModel, bool]:
        existing = await self._table_repo.get_by_fqn(raw.schema_name, raw.table_name)

        if existing:
            existing.row_count = raw.row_count
            existing.size_bytes = raw.size_bytes
            existing.owner = raw.owner
            existing.table_type = raw.table_type
            existing.last_scanned_at = datetime.now(timezone.utc)
            await self._table_repo.session.flush()
            return existing, False

        model = TableModel(
            schema_name=raw.schema_name,
            table_name=raw.table_name,
            table_type=raw.table_type,
            row_count=raw.row_count,
            size_bytes=raw.size_bytes,
            owner=raw.owner,
            last_scanned_at=datetime.now(timezone.utc),
            tags={"names": []},
            usage_examples=[],
            related_tables=[],
        )
        saved = await self._table_repo.save(model)
        log.debug("table_created", fqn=f"{raw.schema_name}.{raw.table_name}")
        return saved, True

    async def _upsert_columns(
        self, table: TableModel, raw_columns: list[RawColumnInfo]
    ) -> int:
        existing_by_name = {
            col.column_name: col
            for col in await self._column_repo.get_by_table(table.id)
        }

        count = 0
        for raw in raw_columns:
            pii_result = detect_pii(raw.column_name, raw.data_type)

            if raw.column_name in existing_by_name:
                col = existing_by_name[raw.column_name]
                col.ordinal_position = raw.ordinal_position
                col.data_type = raw.data_type
                col.is_nullable = raw.is_nullable
                col.default_value = raw.default_value
                if pii_result.is_pii and not col.is_pii:
                    col.is_pii = True
                    col.pii_type = pii_result.pii_type
                await self._column_repo.session.flush()
            else:
                col = ColumnModel(
                    table_id=table.id,
                    column_name=raw.column_name,
                    ordinal_position=raw.ordinal_position,
                    data_type=raw.data_type,
                    is_nullable=raw.is_nullable,
                    default_value=raw.default_value,
                    is_pii=pii_result.is_pii,
                    pii_type=pii_result.pii_type,
                )
                await self._column_repo.save(col)

            count += 1

        return count

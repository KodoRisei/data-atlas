"""
Ingestion orchestration: connects to a target DB, scans schema,
persists metadata, and registers view lineage.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.governance import IngestionRunStatus
from app.ingestion.registry import get_connector
from app.metadata.extractor import MetadataExtractor
from app.persistence.models import IngestionRunModel
from app.persistence.repositories.table import TableRepository
from app.services.lineage import LineageService

log = get_logger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tables = TableRepository(session)

    async def run(
        self,
        db_url: str,
        schemas: list[str] | None = None,
        exclude_schemas: list[str] | None = None,
        infer_view_lineage: bool = True,
    ) -> IngestionRunStatus:
        run = IngestionRunModel(
            source_name=db_url.split("@")[-1] if "@" in db_url else db_url,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self._session.add(run)
        await self._session.flush()

        try:
            connector = get_connector(db_url)
            async with connector:
                raw_result = await connector.scan(
                    schemas=schemas, exclude_schemas=exclude_schemas
                )

            extractor = MetadataExtractor(self._session)
            counts = await extractor.persist(raw_result)

            run.tables_scanned = counts["tables_created"] + counts["tables_updated"]
            run.columns_scanned = counts["columns_upserted"]

            # Auto-detect lineage from view definitions
            if infer_view_lineage:
                lineage_service = LineageService(self._session)
                edges_created = 0
                for raw_table in raw_result.tables:
                    if raw_table.view_definition:
                        table_model = await self._tables.get_by_fqn(
                            raw_table.schema_name, raw_table.table_name
                        )
                        if table_model:
                            edges = await lineage_service.parse_and_register_view_lineage(
                                table_id=table_model.id,
                                view_sql=raw_table.view_definition,
                                schema=raw_table.schema_name,
                            )
                            edges_created += len(edges)

                log.info("view_lineage_registered", edges_created=edges_created)

            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            log.error("ingestion_failed", error=str(exc))
            await self._session.flush()

        await self._session.flush()
        return self._run_to_status(run)

    def _run_to_status(self, run: IngestionRunModel) -> IngestionRunStatus:
        duration = None
        if run.completed_at and run.started_at:
            duration = (run.completed_at - run.started_at).total_seconds()

        return IngestionRunStatus(
            id=run.id,
            source_name=run.source_name,
            status=run.status,
            tables_scanned=run.tables_scanned,
            columns_scanned=run.columns_scanned,
            started_at=run.started_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            error_message=run.error_message,
            duration_seconds=duration,
        )

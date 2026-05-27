"""
AI enrichment service: generates descriptions, business context, and usage examples.
Wraps AI provider calls with caching logic (skip if content already exists).
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import BaseAIProvider
from app.ai.prompts import (
    SYSTEM_PROMPT,
    business_purpose_prompt,
    column_description_prompt,
    table_description_prompt,
    usage_examples_prompt,
)
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.persistence.repositories.column import ColumnRepository
from app.persistence.repositories.table import TableRepository

log = get_logger(__name__)


class AIEnrichmentService:
    def __init__(self, session: AsyncSession, provider: BaseAIProvider) -> None:
        self._tables = TableRepository(session)
        self._columns = ColumnRepository(session)
        self._provider = provider
        self._session = session

    async def enrich_table(
        self,
        table_id: UUID,
        force: bool = False,
    ) -> dict[str, str]:
        """
        Generate and persist table description + business purpose + usage examples.
        Skips fields that already have content unless force=True.
        """
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.")

        columns = await self._columns.get_by_table(table_id)
        col_dicts = [
            {
                "name": c.column_name,
                "type": c.data_type,
                "is_pii": c.is_pii,
            }
            for c in columns
        ]
        col_names = [c.column_name for c in columns]
        results: dict[str, str] = {}

        # Table description
        if force or not table.description:
            log.info(
                "ai_enriching_table_description",
                table=f"{table.schema_name}.{table.table_name}",
                provider=self._provider.provider_name,
            )
            response = await self._provider.complete(
                prompt=table_description_prompt(
                    schema=table.schema_name,
                    table_name=table.table_name,
                    table_type=table.table_type,
                    columns=col_dicts,
                    row_count=table.row_count,
                    existing_description=table.description,
                ),
                system=SYSTEM_PROMPT,
            )
            table.description = response.content.strip()
            results["description"] = table.description

        # Business purpose
        if force or not table.business_purpose:
            response = await self._provider.complete(
                prompt=business_purpose_prompt(
                    schema=table.schema_name,
                    table_name=table.table_name,
                    description=table.description or "",
                    column_names=col_names,
                ),
                system=SYSTEM_PROMPT,
            )
            table.business_purpose = response.content.strip()
            results["business_purpose"] = table.business_purpose

        # Usage examples
        if force or not table.usage_examples:
            response = await self._provider.complete(
                prompt=usage_examples_prompt(
                    schema=table.schema_name,
                    table_name=table.table_name,
                    column_names=col_names,
                ),
                system=SYSTEM_PROMPT,
            )
            # Split on blank line to get two examples
            raw_examples = [
                ex.strip()
                for ex in response.content.strip().split("\n\n")
                if ex.strip()
            ]
            table.usage_examples = raw_examples[:2]
            results["usage_examples"] = str(table.usage_examples)

        await self._session.flush()
        log.info(
            "ai_table_enrichment_complete",
            table=f"{table.schema_name}.{table.table_name}",
            fields_updated=list(results.keys()),
        )
        return results

    async def enrich_columns(
        self,
        table_id: UUID,
        force: bool = False,
    ) -> int:
        """
        Generate descriptions for all columns that don't have one yet.
        Returns the count of columns updated.
        """
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.")

        columns = await self._columns.get_by_table(table_id)
        sibling_names = [c.column_name for c in columns]
        updated = 0

        for col in columns:
            if col.description and not force:
                continue

            response = await self._provider.complete(
                prompt=column_description_prompt(
                    table_name=f"{table.schema_name}.{table.table_name}",
                    column_name=col.column_name,
                    data_type=col.data_type,
                    is_nullable=col.is_nullable,
                    is_pii=col.is_pii,
                    pii_type=col.pii_type,
                    sibling_columns=[n for n in sibling_names if n != col.column_name],
                ),
                system=SYSTEM_PROMPT,
            )
            col.description = response.content.strip()
            updated += 1

        if updated:
            await self._session.flush()
            log.info(
                "ai_column_enrichment_complete",
                table=f"{table.schema_name}.{table.table_name}",
                columns_updated=updated,
            )

        return updated

    async def enrich_all(self, table_id: UUID, force: bool = False) -> dict:
        table_results = await self.enrich_table(table_id, force=force)
        column_count = await self.enrich_columns(table_id, force=force)
        return {
            "table_fields": table_results,
            "columns_enriched": column_count,
        }

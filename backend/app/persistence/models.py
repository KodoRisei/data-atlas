import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TableModel(Base):
    __tablename__ = "tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_type: Mapped[str] = mapped_column(String(50), nullable=False, default="table")
    description: Mapped[str | None] = mapped_column(Text)
    business_purpose: Mapped[str | None] = mapped_column(Text)
    usage_examples: Mapped[list] = mapped_column(JSONB, default=list)
    related_tables: Mapped[list] = mapped_column(JSONB, default=list)
    row_count: Mapped[int | None] = mapped_column(Integer)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    owner: Mapped[str | None] = mapped_column(String(255))
    source_database: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_pii_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    columns: Mapped[list["ColumnModel"]] = relationship(
        "ColumnModel", back_populates="table", cascade="all, delete-orphan"
    )
    outgoing_lineage: Mapped[list["LineageEdgeModel"]] = relationship(
        "LineageEdgeModel",
        foreign_keys="LineageEdgeModel.source_table_id",
        back_populates="source_table",
        cascade="all, delete-orphan",
    )
    incoming_lineage: Mapped[list["LineageEdgeModel"]] = relationship(
        "LineageEdgeModel",
        foreign_keys="LineageEdgeModel.target_table_id",
        back_populates="target_table",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("schema_name", "table_name", name="uq_table_fqn"),)

    @property
    def full_name(self) -> str:
        return f"{self.schema_name}.{self.table_name}"

    @property
    def tag_names(self) -> list[str]:
        return list(self.tags.get("names", []))


class ColumnModel(Base):
    __tablename__ = "columns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ordinal_position: Mapped[int] = mapped_column(Integer, nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    default_value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    pii_type: Mapped[str | None] = mapped_column(String(50))
    statistics: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    table: Mapped["TableModel"] = relationship("TableModel", back_populates="columns")

    __table_args__ = (
        UniqueConstraint("table_id", "column_name", name="uq_column_in_table"),
    )


class LineageEdgeModel(Base):
    __tablename__ = "lineage_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    source_table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="derived_from"
    )
    lineage_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="inferred"
    )
    sql_snippet: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_file: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source_table: Mapped["TableModel"] = relationship(
        "TableModel", foreign_keys=[source_table_id], back_populates="outgoing_lineage"
    )
    target_table: Mapped["TableModel"] = relationship(
        "TableModel", foreign_keys=[target_table_id], back_populates="incoming_lineage"
    )

    __table_args__ = (
        UniqueConstraint(
            "source_table_id", "target_table_id", name="uq_lineage_edge"
        ),
    )


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    source_name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    tables_scanned: Mapped[int] = mapped_column(Integer, default=0)
    columns_scanned: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

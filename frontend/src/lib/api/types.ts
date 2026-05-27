// ── Shared ────────────────────────────────────────────────────────────────────

export type TableType = "table" | "view" | "materialized_view" | "foreign_table";

export type RelationshipType =
  | "derived_from"
  | "references"
  | "depends_on"
  | "copies_from";

export type LineageSource = "sql_view" | "dbt_model" | "manual" | "inferred";

// ── Tables ────────────────────────────────────────────────────────────────────

export interface TableSummary {
  id: string;
  schema_name: string;
  table_name: string;
  table_type: TableType;
  description: string | null;
  row_count: number | null;
  owner: string | null;
  is_pii_flagged: boolean;
  tag_names: string[];
  last_scanned_at: string | null;
}

export interface TableDetail extends TableSummary {
  size_bytes: number | null;
  source_database: string | null;
  business_purpose: string | null;
  usage_examples: string[];
  related_tables: string[];
  column_count: number;
  created_at: string;
  updated_at: string;
}

export interface TableListResponse {
  items: TableSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface TableUpdate {
  description?: string;
  business_purpose?: string;
  usage_examples?: string[];
  owner?: string;
  tag_names?: string[];
}

// ── Columns ───────────────────────────────────────────────────────────────────

export interface ColumnStatistics {
  null_count?: number;
  null_percentage?: number;
  distinct_count?: number;
  min_value?: string;
  max_value?: string;
  avg_value?: number;
  sample_values?: string[];
}

export interface ColumnSummary {
  id: string;
  table_id: string;
  column_name: string;
  ordinal_position: number;
  data_type: string;
  is_nullable: boolean;
  default_value: string | null;
  description: string | null;
  is_pii: boolean;
  pii_type: string | null;
}

export interface ColumnDetail extends ColumnSummary {
  statistics: ColumnStatistics | null;
  created_at: string;
  updated_at: string;
}

// ── Lineage ───────────────────────────────────────────────────────────────────

export interface LineageNode {
  id: string;
  table_id: string;
  schema_name: string;
  table_name: string;
  full_name: string;
  is_pii_flagged: boolean;
  row_count: number | null;
  depth: number;
}

export interface LineageEdge {
  id: string;
  source_table_id: string;
  target_table_id: string;
  source_table_name: string;
  target_table_name: string;
  relationship_type: RelationshipType;
  lineage_source: LineageSource;
  sql_snippet: string | null;
  confidence: number;
  source_file: string | null;
  created_at: string;
}

export interface LineageGraph {
  root_table_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
  upstream_depth: number;
  downstream_depth: number;
}

// ── Impact ────────────────────────────────────────────────────────────────────

export interface ImpactSummary {
  table_id: string;
  table_name: string;
  direct_dependents: number;
  total_downstream: number;
  max_depth: number;
  critical_path: string[];
  affected_tables: LineageNode[];
  blast_radius_score: number;
}

// ── Ingestion ─────────────────────────────────────────────────────────────────

export interface IngestionRunStatus {
  id: string;
  source_name: string;
  status: "running" | "completed" | "failed";
  tables_scanned: number;
  columns_scanned: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  duration_seconds: number | null;
}

import axios from "axios";
import type {
  ColumnDetail,
  ColumnSummary,
  ImpactSummary,
  IngestionRunStatus,
  LineageEdge,
  LineageGraph,
  TableDetail,
  TableListResponse,
  TableSummary,
  TableUpdate,
} from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ── Tables ────────────────────────────────────────────────────────────────────

export const tables = {
  list: (params?: {
    page?: number;
    page_size?: number;
    schema?: string;
    table_type?: string;
    pii_only?: boolean;
  }): Promise<TableListResponse> =>
    api.get("/api/v1/tables", { params }).then((r) => r.data),

  search: (q: string, limit = 20): Promise<TableSummary[]> =>
    api.get("/api/v1/tables/search", { params: { q, limit } }).then((r) => r.data),

  get: (id: string): Promise<TableDetail> =>
    api.get(`/api/v1/tables/${id}`).then((r) => r.data),

  update: (id: string, body: TableUpdate): Promise<TableDetail> =>
    api.patch(`/api/v1/tables/${id}`, body).then((r) => r.data),
};

// ── Columns ───────────────────────────────────────────────────────────────────

export const columns = {
  list: (tableId: string): Promise<ColumnSummary[]> =>
    api.get(`/api/v1/tables/${tableId}/columns`).then((r) => r.data),

  get: (columnId: string): Promise<ColumnDetail> =>
    api.get(`/api/v1/tables/columns/${columnId}`).then((r) => r.data),
};

// ── Lineage ───────────────────────────────────────────────────────────────────

export const lineage = {
  get: (
    tableId: string,
    params?: { upstream_depth?: number; downstream_depth?: number }
  ): Promise<LineageGraph> =>
    api.get(`/api/v1/lineage/${tableId}`, { params }).then((r) => r.data),

  createEdge: (body: {
    source_table_id: string;
    target_table_id: string;
    relationship_type?: string;
    lineage_source?: string;
  }): Promise<LineageEdge> =>
    api.post("/api/v1/lineage/edges", body).then((r) => r.data),
};

// ── Impact ────────────────────────────────────────────────────────────────────

export const impact = {
  analyze: (tableId: string): Promise<ImpactSummary> =>
    api.get(`/api/v1/impact/${tableId}`).then((r) => r.data),
};

// ── Ingestion ─────────────────────────────────────────────────────────────────

export const ingestion = {
  scan: (body: {
    db_url: string;
    schemas?: string[];
    exclude_schemas?: string[];
    infer_view_lineage?: boolean;
  }): Promise<IngestionRunStatus> =>
    api.post("/api/v1/ingestion/scan", body).then((r) => r.data),

  enrich: (tableId: string, force = false): Promise<Record<string, unknown>> =>
    api.post(`/api/v1/ingestion/enrich/${tableId}`, null, { params: { force } }).then((r) => r.data),
};

export default api;

export interface BoundingBox { x: number; y: number; width: number; height: number }
export type PdfEvidence = { kind: "pdf"; page: number; bbox?: BoundingBox | null };
export type ExcelEvidence = { kind: "excel"; sheet: string; cell_range: string };
export interface Evidence { evidence_id: string; document_id: string; template_id?: string | null; template_version?: number | null; rule_id?: string | null; source_text?: string | null; confidence: number; source: PdfEvidence | ExcelEvidence }

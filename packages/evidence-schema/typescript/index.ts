export interface BoundingBox { x: number; y: number; width: number; height: number }
export type PdfEvidence = { kind: "pdf"; page: number; bbox?: BoundingBox | null };
export type ExcelEvidence = { kind: "excel"; sheet: string; cell_range: string };
export interface Evidence { evidence_id: string; document_id: string; template_id?: string | null; template_version?: number | null; rule_id?: string | null; source_text?: string | null; confidence: number; source: PdfEvidence | ExcelEvidence }
export interface SourceReference { document_id: string; preview_id?: string | null; storage_bucket?: string | null; storage_key?: string | null; page?: number | null; sheet?: string | null; cell_range?: string | null; bbox?: BoundingBox | null }
export interface TemplateRuleReference { template_id: string; template_version_id: string; field_id?: string | null; extraction_rule_id?: string | null }
export interface RawExtractionEvidence { evidence_id: string; extraction_job_id: string; source: SourceReference; template_rule?: TemplateRuleReference | null; confidence?: number | null; raw_text?: string | null }

export interface BoundingBox { x: number; y: number; width: number; height: number }
export interface PdfBoundingBox { x0: number; y0: number; x1: number; y1: number }
export type PdfEvidence = { kind: "pdf"; page: number; bbox?: BoundingBox | null };
export type ExcelEvidence = { kind: "excel"; sheet: string; cell_range: string };
export interface Evidence { evidence_id: string; document_id: string; template_id?: string | null; template_version?: number | null; rule_id?: string | null; source_text?: string | null; confidence: number; source: PdfEvidence | ExcelEvidence }
export interface SourceReference { document_id: string; preview_id?: string | null; storage_bucket?: string | null; storage_key?: string | null; page?: number | null; sheet?: string | null; cell_range?: string | null; bbox?: BoundingBox | null }
export interface TemplateRuleReference { template_id: string; template_version_id: string; field_id?: string | null; extraction_rule_id?: string | null }
export interface ExtractionEvidenceConfidence { confidence: number; factors: string[] }
export interface PdfExtractionEvidence { evidence_type: "pdf"; document_id: string; page_number: number; bbox?: PdfBoundingBox | null; source_text?: string | null; rule_id?: string | null; rule_strategy?: string | null; confidence: number }
export interface CellRange { sheet_name: string; cell_range: string }
export interface ExcelExtractionEvidence { evidence_type: "excel"; document_id: string; sheet_name: string; cell_range?: string | null; source_value?: string | number | boolean | null; rule_id?: string | null; rule_strategy?: string | null; confidence: number }
export interface RawExtractionEvidence { evidence_id: string; extraction_job_id: string; source: SourceReference; template_rule?: TemplateRuleReference | null; confidence?: number | null; raw_text?: string | null }

export interface BoundingBox { x: number; y: number; width: number; height: number }
export type PdfSelection = { kind: "pdf_text" | "pdf_area"; page: number; selected_text?: string | null; bbox: BoundingBox };
export type ExcelSelection = { kind: "excel_cell" | "excel_column" | "excel_table"; sheet: string; range: string; header?: string | null };
export interface Annotation { annotation_id: string; template_id: string; template_version: number; document_id: string; target_field: string; selection: PdfSelection | ExcelSelection }

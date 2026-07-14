export type DocumentType = "balancete" | "guia_inss" | "guia_fgts" | "folha_pagamento" | "relatorio_fiscal" | "relatorio_contabil" | "extrato" | "outro" | "desconhecido";
export type DocumentStatus = "imported" | "classified" | "ambiguous" | "missing" | "confirmed" | "rejected" | "extracted" | "error";

export interface BoundingBox { x: number; y: number; width: number; height: number }
export interface Evidence { document_id: string; page?: number | null; row?: number | null; column?: string | null; cell?: string | null; text?: string | null; bounding_box?: BoundingBox | null }
export interface PreviewBoundingBox { x0: number; y0: number; x1: number; y1: number }
export type DocumentPreviewStatus = "preview_pending" | "preview_processing" | "preview_ready" | "preview_failed";
export type ParsingJobStatus = "pending" | "processing" | "completed" | "failed";
export interface PdfToken { token_id: string; text: string; bbox: PreviewBoundingBox; confidence?: number | null }
export interface PdfLine { line_id: string; text: string; bbox: PreviewBoundingBox; tokens: PdfToken[] }
export interface PdfTextBlock { block_id: string; text: string; bbox: PreviewBoundingBox; confidence?: number | null; source: string }
export interface PdfTableCandidate { table_id: string; bbox: PreviewBoundingBox; rows: unknown[]; columns: unknown[]; confidence: number }
export interface PdfPagePreview { page_number: number; width: number; height: number; rotation: number; text_blocks: PdfTextBlock[]; lines: PdfLine[]; tables: PdfTableCandidate[] }
export interface PreviewSummary { page_count: number; sheet_count: number; text_block_count: number; table_count: number }
export interface PdfDocumentPreview { document_id: string; file_format: "PDF"; parser_version: string; generated_at: string; requires_ocr: boolean; ocr_reason?: string | null; pages: PdfPagePreview[]; summary: PreviewSummary }
export interface ExcelCellPreview { cell_id: string; address: string; row: number; column: number; column_letter: string; value: unknown; raw_value: unknown; data_type: string; is_merged: boolean; merged_range?: string | null }
export interface ExcelMergedRange { range: string; start_row: number; start_column: number; end_row: number; end_column: number }
export interface ExcelDetectedHeader { row: number; values: string[]; confidence: number }
export interface ExcelTableCandidate { table_id: string; range: string; header_row: number; start_row: number; end_row: number; confidence: number }
export interface ExcelSheetPreview { sheet_id: string; name: string; index: number; max_row: number; max_column: number; cells: ExcelCellPreview[]; merged_cells: ExcelMergedRange[]; detected_headers: ExcelDetectedHeader[]; detected_tables: ExcelTableCandidate[] }
export interface ExcelDocumentPreview { document_id: string; file_format: "XLSX" | "XLS"; parser_version: string; generated_at: string; requires_ocr: false; sheets: ExcelSheetPreview[]; summary: PreviewSummary }
export type ParsedDocumentPreview = PdfDocumentPreview | ExcelDocumentPreview;
export interface ParsingJob { parsing_job_id: string; document_id: string; preview_id: string; status: ParsingJobStatus; requested_by: string; started_at?: string | null; finished_at?: string | null; error_message?: string | null; parser_worker_version?: string | null }
export type DocumentSelection =
  | { selection_type: "pdf_text_block" | "pdf_line"; document_id: string; page_number: number; text: string; bbox: PreviewBoundingBox; source: "preview" }
  | { selection_type: "pdf_area"; document_id: string; page_number: number; bbox: PreviewBoundingBox; source: "user_area_selection" }
  | { selection_type: "pdf_table_candidate"; document_id: string; page_number: number; table_id: string; bbox: PreviewBoundingBox; confidence: number; source: "preview" }
  | { selection_type: "excel_cell"; document_id: string; sheet_name: string; sheet_index: number; cell: { address: string; row: number; column: number; column_letter: string; value: unknown; raw_value?: unknown; data_type?: string }; source: "preview" }
  | { selection_type: "excel_column"; document_id: string; sheet_name: string; sheet_index: number; column: number; column_letter: string; header?: string | null; source: "user_column_selection" }
  | { selection_type: "excel_row"; document_id: string; sheet_name: string; sheet_index: number; row: number; source: "user_row_selection" }
  | { selection_type: "excel_range"; document_id: string; sheet_name: string; sheet_index: number; range: { start_cell: string; end_cell: string; start_row: number; end_row: number; start_column: number; end_column: number }; source: "user_range_selection" }
  | { selection_type: "excel_table_candidate"; document_id: string; sheet_name: string; sheet_index: number; table_id: string; range: string; header_row: number; start_row: number; end_row: number; confidence: number; source: "preview" };
export type EvidenceHighlight =
  | { evidence_type: "pdf"; page_number: number; bbox: PreviewBoundingBox; label: string }
  | { evidence_type: "excel"; sheet_name: string; cell_range: string; label: string };
export interface Document { document_id: string; client_id: string; competence_id: string; filename: string; original_filename: string; extension: string; mime_type: string; size_bytes: number; sha256_hash: string; storage_bucket: string; storage_key: string; document_type: DocumentType; status: DocumentStatus; classification_confidence?: number | null; created_at: string; updated_at: string; metadata: Record<string, unknown> }

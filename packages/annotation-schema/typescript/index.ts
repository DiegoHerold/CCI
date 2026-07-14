export type AnnotationType =
  | "pdf_text_block"
  | "pdf_line"
  | "pdf_token"
  | "pdf_area"
  | "pdf_table_candidate"
  | "excel_cell"
  | "excel_column"
  | "excel_row"
  | "excel_range"
  | "excel_table_candidate";

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface AnnotationTargetField {
  field_id: string;
  field_path: string;
}

export interface TemplateAnnotation {
  id: string;
  template_id: string;
  template_version_id?: string | null;
  document_id: string;
  field_id: string;
  annotation_type: AnnotationType;
  source_preview_id?: string | null;
  selected_text?: string | null;
  selection_payload: Record<string, unknown>;
}

export type Annotation = TemplateAnnotation;

export interface CreateAnnotationRequest {
  template_version_id?: string | null;
  field_id: string;
  document_id: string;
  annotation_type: AnnotationType;
  source_preview_id?: string | null;
  selected_text?: string | null;
  selection_payload: Record<string, unknown>;
}

export interface CreateAnnotationResponse {
  annotation: TemplateAnnotation;
}

export interface CreateAnnotationWithRuleRequest extends CreateAnnotationRequest {
  generate_rule: boolean;
  rule_strategy?: string | null;
  rule_config?: Record<string, unknown> | null;
}

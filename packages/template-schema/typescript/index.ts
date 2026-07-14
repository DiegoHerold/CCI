export type TemplateStatus = "draft" | "active" | "inactive" | "archived";
export type TemplateVersionStatus = "draft" | "published" | "archived";
export type TemplateMatchingStatus = "matched" | "not_found" | "ambiguous" | "failed";
export type TemplateFileFormat = "PDF" | "XLSX" | "XLS" | "CSV" | "TXT" | "DOCX" | "XML" | "IMAGE";
export type TemplateFormat = TemplateFileFormat;
export type TemplateStructureType = "text" | "table" | "hierarchical" | "form" | "mixed" | "unknown";
export type IdentificationSignalType =
  | "contains_text"
  | "contains_any_text"
  | "contains_all_text"
  | "not_contains_text"
  | "regex"
  | "file_format"
  | "sheet_name"
  | "column_header"
  | "table_header"
  | "page_count_range"
  | "has_cnpj"
  | "has_date"
  | "has_currency_values"
  | "structure_hint";
export type ExtractionStrategy =
  | "find_near_label"
  | "fixed_bbox"
  | "pdf_area_table"
  | "pdf_column_by_x_position"
  | "hierarchical_lines"
  | "excel_cell_address"
  | "excel_column_by_header"
  | "excel_range_table"
  | "excel_sheet_by_name"
  | "regex_from_text";

export interface TemplateCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  status: string;
}

export interface IdentificationSignal {
  id?: string | null;
  template_id?: string | null;
  signal_type: IdentificationSignalType;
  weight: number;
  value: string;
  required: boolean;
  negative: boolean;
}

export interface Template {
  template_id: string;
  name: string;
  description?: string | null;
  category_id: string;
  file_format: TemplateFileFormat;
  structure_type: TemplateStructureType;
  status: TemplateStatus;
  active_version_id?: string | null;
}

export interface TemplateVersion {
  id: string;
  template_id: string;
  version_number: number;
  status: TemplateVersionStatus;
  snapshot: Record<string, unknown>;
}

export interface ExtractionRule {
  id?: string | null;
  template_id?: string | null;
  template_version_id?: string | null;
  field_id: string;
  rule_type?: string | null;
  strategy: ExtractionStrategy;
  config: Record<string, unknown>;
  confidence_hint?: number | null;
  created_from_annotation_id?: string | null;
}

export interface TemplateSummary extends Template {
  field_count: number;
  extraction_rule_count: number;
}

export interface TemplateDetail extends Template {
  identification_signals: IdentificationSignal[];
  versions: TemplateVersion[];
}

export interface TemplateBuilderState {
  template: TemplateDetail;
  active_version?: TemplateVersion | null;
  draft_version?: TemplateVersion | null;
  fields: Record<string, unknown>[];
  annotations: Record<string, unknown>[];
  extraction_rules: ExtractionRule[];
  identification_signals: IdentificationSignal[];
}

export interface TemplateBuilderSaveRequest {
  fields: Record<string, unknown>[];
  annotations: Record<string, unknown>[];
  extraction_rules: ExtractionRule[];
}

export interface DocumentProfile {
  document_id: string;
  client_id?: string | null;
  competence_id?: string | null;
  file_format: TemplateFileFormat;
  mime_type?: string | null;
  original_filename?: string | null;
  page_count: number;
  sheet_count: number;
  requires_ocr: boolean;
  text_sample: string;
  normalized_text_sample: string;
  detected_keywords: string[];
  detected_regex_patterns: string[];
  has_cnpj: boolean;
  has_dates: boolean;
  has_currency_values: boolean;
  has_tables: boolean;
  structure_hints: string[];
  sheet_names: string[];
  detected_headers: string[];
}

export interface TemplateMatchingRequest {
  force_reprocess?: boolean;
  category_hint?: string | null;
  max_candidates?: number | null;
}

export interface TemplateMatchingCandidate {
  template_id: string;
  template_version_id?: string | null;
  category_id?: string | null;
  template_name?: string | null;
  category_name?: string | null;
  score: number;
  rank_position: number;
  matched_signals: string[];
  missing_required_signals: string[];
  negative_matches: string[];
  score_details: Record<string, unknown>;
}

export interface TemplateMatchingResult {
  matching_run_id: string;
  document_id: string;
  status: TemplateMatchingStatus;
  matched_template_id?: string | null;
  matched_template_version_id?: string | null;
  matched_category_id?: string | null;
  confidence: number;
  decision_reason: string;
  manual_override: boolean;
  candidates: TemplateMatchingCandidate[];
}

export type TemplateMatchingRun = TemplateMatchingResult;

export interface SuggestedTemplate {
  name: string;
  category: string;
  file_format: string;
  structure_type: string;
}

export interface SuggestedField {
  field_path: string;
  label: string;
  field_type: string;
  important: boolean;
  required: boolean;
  raw_sample?: unknown;
  normalized_preview?: string | null;
  display_value?: string | null;
  confidence: number;
}

export interface SuggestedArray {
  field_path: string;
  label: string;
  item_fields: string[];
  confidence: number;
}

export interface SuggestedRule {
  field_path: string;
  strategy: ExtractionStrategy;
  config: Record<string, unknown>;
  confidence: number;
}

export interface TemplateSuggestion {
  document_id: string;
  suggested_template: SuggestedTemplate;
  suggested_fields: SuggestedField[];
  suggested_arrays: SuggestedArray[];
  suggested_rules: SuggestedRule[];
  warnings: string[];
}

export interface RulePreviewNormalization {
  field_path: string;
  raw_value?: unknown;
  normalized_value?: unknown;
  display_value?: string | null;
  status: string;
  confidence: number;
  evidence: Record<string, unknown>;
}

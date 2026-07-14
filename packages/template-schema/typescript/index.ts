export type TemplateStatus = "draft" | "active" | "inactive" | "archived";
export type TemplateVersionStatus = "draft" | "published" | "archived";
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

export interface TemplateSummary extends Template {
  field_count: number;
  extraction_rule_count: number;
}

export interface TemplateDetail extends Template {
  identification_signals: IdentificationSignal[];
  versions: TemplateVersion[];
}

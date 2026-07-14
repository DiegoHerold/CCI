import type { DocumentSelection, EvidenceHighlight } from "@/features/document-viewer/types/selection";
import type { BoundingBox } from "@/features/document-viewer/types/preview";

export type TemplateFileFormat = "PDF" | "XLSX" | "XLS" | "CSV" | "TXT" | "DOCX" | "XML" | "IMAGE";
export type TemplateStructureType = "text" | "table" | "hierarchical" | "form" | "mixed" | "unknown";
export type TemplateStatus = "draft" | "active" | "inactive" | "archived";
export type TemplateVersionStatus = "draft" | "published" | "archived";
export type FieldType =
  | "text"
  | "number"
  | "money"
  | "date"
  | "month"
  | "cnpj"
  | "cpf"
  | "boolean"
  | "percentage"
  | "account_code"
  | "object"
  | "array"
  | "table"
  | "calculated"
  | "unknown";
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

export interface TemplateSummary {
  templateId: string;
  name: string;
  description?: string | null;
  categoryId: string;
  fileFormat: TemplateFileFormat;
  structureType: TemplateStructureType;
  status: TemplateStatus;
  activeVersionId?: string | null;
  createdBy?: string;
}

export interface TemplateField {
  id: string;
  templateId: string;
  parentFieldId?: string | null;
  fieldPath: string;
  label: string;
  description?: string | null;
  fieldType: FieldType;
  isRequired: boolean;
  important?: boolean;
  isRepeated: boolean;
  isObject: boolean;
  isArray: boolean;
  orderIndex: number;
  status: string;
}

export interface TemplateAnnotation {
  id: string;
  templateId: string;
  templateVersionId?: string | null;
  fieldId: string;
  documentId: string;
  annotationType: DocumentSelection["selection_type"];
  sourcePreviewId?: string | null;
  selectedText?: string | null;
  selectionPayload: DocumentSelection | Record<string, unknown>;
}

export interface ExtractionRule {
  id: string;
  templateId: string;
  templateVersionId?: string | null;
  fieldId: string;
  ruleType?: string | null;
  strategy: ExtractionStrategy;
  config: Record<string, unknown>;
  confidenceHint?: number | null;
  createdFromAnnotationId?: string | null;
}

export interface IdentificationSignal {
  id: string;
  templateId: string;
  signalType: string;
  weight: number;
  value: string;
  required: boolean;
  negative: boolean;
}

export interface TemplateVersion {
  id: string;
  templateId: string;
  versionNumber: number;
  status: TemplateVersionStatus;
  snapshot: Record<string, unknown>;
}

export interface TemplateBuilderState {
  template: TemplateSummary;
  activeVersion?: TemplateVersion | null;
  draftVersion?: TemplateVersion | null;
  fields: TemplateField[];
  annotations: TemplateAnnotation[];
  extractionRules: ExtractionRule[];
  identificationSignals: IdentificationSignal[];
}

export interface TemplateSuggestionResponse {
  documentId: string;
  suggestedTemplate: {
    name: string;
    category: string;
    fileFormat: TemplateFileFormat | string;
    structureType: TemplateStructureType | string;
  };
  suggestedFields: Array<{
    fieldPath: string;
    label: string;
    fieldType: FieldType;
    important: boolean;
    required: boolean;
    rawSample?: unknown;
    normalizedPreview?: string | null;
    displayValue?: string | null;
    confidence: number;
  }>;
  suggestedArrays: Array<{
    fieldPath: string;
    label: string;
    itemFields: string[];
    confidence: number;
  }>;
  suggestedRules: Array<{
    fieldPath: string;
    strategy: ExtractionStrategy;
    config: Record<string, unknown>;
    confidence: number;
  }>;
  warnings: string[];
}

export interface RulePreviewNormalizationResponse {
  fieldPath: string;
  rawValue?: unknown;
  normalizedValue?: unknown;
  displayValue?: string | null;
  status: string;
  confidence: number;
  evidence: Record<string, unknown>;
}

export interface FieldTreeNode {
  key: string;
  label: string;
  path: string;
  field?: TemplateField;
  children: FieldTreeNode[];
}

export interface AnnotationWithRuleResponse {
  annotation: TemplateAnnotation;
  extractionRule?: ExtractionRule | null;
  suggestedStrategy?: ExtractionStrategy | null;
  suggestedConfig: Record<string, unknown>;
}

export type BuilderStatus =
  | "loading_document"
  | "loading_preview"
  | "loading_template"
  | "template_loaded"
  | "saving_annotation"
  | "saving_rule"
  | "publishing_version"
  | "preview_failed"
  | "requires_ocr"
  | "error";

export function annotationToEvidence(annotation: TemplateAnnotation, field?: TemplateField): EvidenceHighlight | null {
  const payload = annotation.selectionPayload as Record<string, unknown>;
  const label = field?.fieldPath ?? annotation.fieldId;
  if (annotation.annotationType.startsWith("pdf_") && typeof payload.page_number === "number" && payload.bbox) {
    return { evidence_type: "pdf", page_number: payload.page_number, bbox: payload.bbox as BoundingBox, label };
  }
  if (annotation.annotationType === "excel_cell" && typeof payload.sheet_name === "string") {
    const cell = payload.cell as { address?: string } | undefined;
    return { evidence_type: "excel", sheet_name: payload.sheet_name, cell_range: cell?.address ?? "", label };
  }
  if (annotation.annotationType === "excel_column" && typeof payload.sheet_name === "string" && typeof payload.column_letter === "string") {
    return { evidence_type: "excel", sheet_name: payload.sheet_name, cell_range: `${payload.column_letter}1:${payload.column_letter}9999`, label };
  }
  if ((annotation.annotationType === "excel_range" || annotation.annotationType === "excel_table_candidate") && typeof payload.sheet_name === "string") {
    const range = typeof payload.range === "string" ? payload.range : "";
    return { evidence_type: "excel", sheet_name: payload.sheet_name, cell_range: range, label };
  }
  return null;
}

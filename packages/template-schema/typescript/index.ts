export type TemplateFormat = "pdf" | "xlsx" | "xls" | "csv" | "image" | "other";
export type TemplateStructureType = "flat" | "hierarchical" | "tabular" | "mixed";

export interface TemplateIdentificationSignal {
  kind: "filename" | "text" | "sheet" | "header" | "layout";
  value: string;
  weight?: number;
}

export interface TemplateVersion {
  template_id: string;
  name: string;
  category: string;
  format: TemplateFormat;
  structure_type: TemplateStructureType;
  version: number;
  status: "draft" | "published" | "archived";
  identification_signals: TemplateIdentificationSignal[];
  field_paths: string[];
}

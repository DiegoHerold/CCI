import type { DocumentSelection } from "@/features/document-viewer/types/selection";
import type { ExtractionStrategy, TemplateField } from "../types/templateBuilder";

export function selectionLabel(selection: DocumentSelection | null) {
  if (!selection) return "Nenhuma selecao";
  return selection.selection_type.replaceAll("_", " ");
}

export function selectedText(selection: DocumentSelection | null) {
  if (!selection) return null;
  if ("text" in selection) return selection.text;
  if ("cell" in selection) return String(selection.cell.value ?? selection.cell.raw_value ?? "");
  if ("header" in selection) return selection.header ?? null;
  return null;
}

export function suggestStrategy(selection: DocumentSelection | null, field?: TemplateField | null): ExtractionStrategy | null {
  if (!selection) return null;
  if (selection.selection_type === "pdf_text_block" || selection.selection_type === "pdf_line") {
    return selectedText(selection)?.includes(":") ? "find_near_label" : "fixed_bbox";
  }
  if (selection.selection_type === "pdf_area") return "fixed_bbox";
  if (selection.selection_type === "pdf_table_candidate") return "pdf_area_table";
  if (selection.selection_type === "excel_cell") return "excel_cell_address";
  if (selection.selection_type === "excel_column") return "excel_column_by_header";
  if (selection.selection_type === "excel_range" || selection.selection_type === "excel_table_candidate") return "excel_range_table";
  if (field?.isArray) return "excel_range_table";
  return null;
}

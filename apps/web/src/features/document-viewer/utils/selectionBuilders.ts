import type {
  ExcelCellPreview,
  ExcelSheetPreview,
  ExcelTableCandidate,
  PdfLine,
  PdfTableCandidate,
  PdfTextBlock,
  BoundingBox,
} from "../types/preview";
import type { DocumentSelection } from "../types/selection";
import { cellAddress, columnLetter } from "./excelCoordinates";

export function buildPdfTextSelection(
  documentId: string,
  pageNumber: number,
  item: PdfTextBlock | PdfLine,
  type: "pdf_text_block" | "pdf_line",
): DocumentSelection {
  return {
    selection_type: type,
    document_id: documentId,
    page_number: pageNumber,
    text: item.text,
    bbox: item.bbox,
    source: "preview",
  };
}

export function buildPdfAreaSelection(documentId: string, pageNumber: number, bbox: BoundingBox): DocumentSelection {
  return {
    selection_type: "pdf_area",
    document_id: documentId,
    page_number: pageNumber,
    bbox,
    source: "user_area_selection",
  };
}

export function buildPdfTableSelection(
  documentId: string,
  pageNumber: number,
  table: PdfTableCandidate,
): DocumentSelection {
  return {
    selection_type: "pdf_table_candidate",
    document_id: documentId,
    page_number: pageNumber,
    table_id: table.table_id,
    bbox: table.bbox,
    confidence: table.confidence,
    source: "preview",
  };
}

export function buildExcelCellSelection(documentId: string, sheet: ExcelSheetPreview, cell: ExcelCellPreview): DocumentSelection {
  return {
    selection_type: "excel_cell",
    document_id: documentId,
    sheet_name: sheet.name,
    sheet_index: sheet.index,
    cell: {
      address: cell.address,
      row: cell.row,
      column: cell.column,
      column_letter: cell.column_letter,
      value: cell.value,
      raw_value: cell.raw_value,
      data_type: cell.data_type,
    },
    source: "preview",
  };
}

export function buildExcelColumnSelection(
  documentId: string,
  sheet: ExcelSheetPreview,
  column: number,
  header?: string | null,
): DocumentSelection {
  return {
    selection_type: "excel_column",
    document_id: documentId,
    sheet_name: sheet.name,
    sheet_index: sheet.index,
    column,
    column_letter: columnLetter(column),
    header,
    source: "user_column_selection",
  };
}

export function buildExcelRowSelection(documentId: string, sheet: ExcelSheetPreview, row: number): DocumentSelection {
  return {
    selection_type: "excel_row",
    document_id: documentId,
    sheet_name: sheet.name,
    sheet_index: sheet.index,
    row,
    source: "user_row_selection",
  };
}

export function buildExcelRangeSelection(
  documentId: string,
  sheet: ExcelSheetPreview,
  start: { row: number; column: number },
  end: { row: number; column: number },
): DocumentSelection {
  const startRow = Math.min(start.row, end.row);
  const endRow = Math.max(start.row, end.row);
  const startColumn = Math.min(start.column, end.column);
  const endColumn = Math.max(start.column, end.column);
  return {
    selection_type: "excel_range",
    document_id: documentId,
    sheet_name: sheet.name,
    sheet_index: sheet.index,
    range: {
      start_cell: cellAddress(startRow, startColumn),
      end_cell: cellAddress(endRow, endColumn),
      start_row: startRow,
      end_row: endRow,
      start_column: startColumn,
      end_column: endColumn,
    },
    source: "user_range_selection",
  };
}

export function buildExcelTableSelection(
  documentId: string,
  sheet: ExcelSheetPreview,
  table: ExcelTableCandidate,
): DocumentSelection {
  return {
    selection_type: "excel_table_candidate",
    document_id: documentId,
    sheet_name: sheet.name,
    sheet_index: sheet.index,
    table_id: table.table_id,
    range: table.range,
    header_row: table.header_row,
    start_row: table.start_row,
    end_row: table.end_row,
    confidence: table.confidence,
    source: "preview",
  };
}

import type { BoundingBox, ExcelCellPreview } from "./preview";

export type SelectionType =
  | "pdf_text_block"
  | "pdf_line"
  | "pdf_area"
  | "pdf_table_candidate"
  | "excel_cell"
  | "excel_column"
  | "excel_row"
  | "excel_range"
  | "excel_table_candidate";

export type DocumentSelection =
  | {
      selection_type: "pdf_text_block" | "pdf_line";
      document_id: string;
      page_number: number;
      text: string;
      bbox: BoundingBox;
      source: "preview";
    }
  | {
      selection_type: "pdf_area";
      document_id: string;
      page_number: number;
      bbox: BoundingBox;
      source: "user_area_selection";
    }
  | {
      selection_type: "pdf_table_candidate";
      document_id: string;
      page_number: number;
      table_id: string;
      bbox: BoundingBox;
      confidence: number;
      source: "preview";
    }
  | {
      selection_type: "excel_cell";
      document_id: string;
      sheet_name: string;
      sheet_index: number;
      cell: Pick<ExcelCellPreview, "address" | "row" | "column" | "column_letter" | "value" | "raw_value" | "data_type">;
      source: "preview";
    }
  | {
      selection_type: "excel_column";
      document_id: string;
      sheet_name: string;
      sheet_index: number;
      column: number;
      column_letter: string;
      header?: string | null;
      source: "user_column_selection";
    }
  | {
      selection_type: "excel_row";
      document_id: string;
      sheet_name: string;
      sheet_index: number;
      row: number;
      source: "user_row_selection";
    }
  | {
      selection_type: "excel_range";
      document_id: string;
      sheet_name: string;
      sheet_index: number;
      range: {
        start_cell: string;
        end_cell: string;
        start_row: number;
        end_row: number;
        start_column: number;
        end_column: number;
      };
      source: "user_range_selection";
    }
  | {
      selection_type: "excel_table_candidate";
      document_id: string;
      sheet_name: string;
      sheet_index: number;
      table_id: string;
      range: string;
      header_row: number;
      start_row: number;
      end_row: number;
      confidence: number;
      source: "preview";
    };

export type EvidenceHighlight =
  | {
      evidence_type: "pdf";
      page_number: number;
      bbox: BoundingBox;
      label: string;
    }
  | {
      evidence_type: "excel";
      sheet_name: string;
      cell_range: string;
      label: string;
    };

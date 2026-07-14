import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DocumentViewerShell } from "./DocumentViewerShell";
import type { DocumentRecord, ExcelDocumentPreview, PdfDocumentPreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

const documentRecord: DocumentRecord = {
  documentId: "doc-1",
  clientId: "client-1",
  competenceId: "competence-1",
  originalFilename: "balancete.pdf",
  fileFormat: "PDF",
  status: "preview_ready",
};

const pdfPreview: PdfDocumentPreview = {
  document_id: "doc-1",
  file_format: "PDF",
  parser_version: "1.0.0",
  generated_at: "2026-07-14T00:00:00Z",
  requires_ocr: false,
  pages: [
    {
      page_number: 1,
      width: 400,
      height: 300,
      rotation: 0,
      text_blocks: [
        {
          block_id: "block-1",
          text: "CNPJ: 00.000.000/0001-00",
          bbox: { x0: 20, y0: 30, x1: 190, y1: 48 },
          confidence: null,
          source: "pdf_text_layer",
        },
      ],
      lines: [
        {
          line_id: "line-1",
          text: "Conta Descrição Saldo Atual",
          bbox: { x0: 20, y0: 70, x1: 230, y1: 90 },
          tokens: [],
        },
      ],
      tables: [
        {
          table_id: "table-1",
          bbox: { x0: 20, y0: 100, x1: 360, y1: 240 },
          rows: [],
          columns: [],
          confidence: 0.75,
        },
      ],
    },
  ],
  summary: { page_count: 1, sheet_count: 0, text_block_count: 1, table_count: 1 },
};

const excelPreview: ExcelDocumentPreview = {
  document_id: "doc-2",
  file_format: "XLSX",
  parser_version: "1.0.0",
  generated_at: "2026-07-14T00:00:00Z",
  requires_ocr: false,
  sheets: [
    {
      sheet_id: "sheet-1",
      name: "Balancete",
      index: 0,
      max_row: 2,
      max_column: 3,
      cells: [
        { cell_id: "a1", address: "A1", row: 1, column: 1, column_letter: "A", value: "Conta", raw_value: "Conta", data_type: "text", is_merged: false, merged_range: null },
        { cell_id: "b1", address: "B1", row: 1, column: 2, column_letter: "B", value: "Descrição", raw_value: "Descrição", data_type: "text", is_merged: false, merged_range: null },
        { cell_id: "c1", address: "C1", row: 1, column: 3, column_letter: "C", value: "Saldo Atual", raw_value: "Saldo Atual", data_type: "text", is_merged: false, merged_range: null },
        { cell_id: "a2", address: "A2", row: 2, column: 1, column_letter: "A", value: "1.1.01", raw_value: "1.1.01", data_type: "text", is_merged: false, merged_range: null },
        { cell_id: "c2", address: "C2", row: 2, column: 3, column_letter: "C", value: 15000, raw_value: 15000, data_type: "number", is_merged: false, merged_range: null },
      ],
      merged_cells: [],
      detected_headers: [{ row: 1, values: ["Conta", "Descrição", "Saldo Atual"], confidence: 0.85 }],
      detected_tables: [{ table_id: "table-xls", range: "A1:C2", header_row: 1, start_row: 2, end_row: 2, confidence: 0.8 }],
    },
  ],
  summary: { page_count: 0, sheet_count: 1, text_block_count: 0, table_count: 1 },
};

function renderShell({
  preview = pdfPreview,
  state = "preview_ready",
  evidences = [],
}: {
  preview?: PdfDocumentPreview | ExcelDocumentPreview | null;
  state?: "preview_ready" | "requires_ocr" | "loading_preview" | "preview_failed" | "preview_missing";
  evidences?: EvidenceHighlight[];
} = {}) {
  let currentSelection: DocumentSelection | null = null;
  const onSelect = vi.fn((selection: DocumentSelection) => {
    currentSelection = selection;
    rerender(build(currentSelection));
  });
  const build = (selection: DocumentSelection | null) => (
    <DocumentViewerShell
      document={documentRecord}
      preview={preview}
      state={state}
      status={state === "preview_failed" ? "preview_failed" : "preview_ready"}
      error={state === "preview_failed" ? "falha simulada" : null}
      selection={selection}
      evidences={evidences}
      onSelect={onSelect}
      onClearSelection={() => {
        currentSelection = null;
        rerender(build(null));
      }}
      onReload={vi.fn()}
      onRequestPreview={vi.fn()}
      onReprocessPreview={vi.fn()}
    />
  );
  const { rerender } = render(build(currentSelection));
  return { onSelect };
}

describe("DocumentViewerShell", () => {
  it("renderiza preview PDF e seleciona bloco de texto", async () => {
    const actor = userEvent.setup();
    renderShell();

    expect(screen.getByRole("region", { name: /Página PDF 1/i })).toBeInTheDocument();
    await actor.click(screen.getByLabelText(/Selecionar bloco/i));

    expect(screen.getByText("CNPJ: 00.000.000/0001-00")).toBeInTheDocument();
    expect(screen.getByText(/pdf_text_block/i)).toBeInTheDocument();
  });

  it("seleciona tabela candidata PDF e renderiza evidência", async () => {
    const actor = userEvent.setup();
    renderShell({ evidences: [{ evidence_type: "pdf", page_number: 1, bbox: { x0: 20, y0: 30, x1: 80, y1: 48 }, label: "empresa.cnpj" }] });

    expect(screen.getByTestId("pdf-evidence-highlight")).toBeInTheDocument();
    await actor.click(screen.getByLabelText(/Selecionar tabela candidata/i));

    expect(screen.getByText(/pdf_table_candidate/i)).toBeInTheDocument();
    expect(screen.getByText(/table-1/i)).toBeInTheDocument();
  });

  it("renderiza Excel e seleciona célula e coluna", async () => {
    const actor = userEvent.setup();
    renderShell({ preview: excelPreview });

    expect(screen.getByText("Balancete")).toBeInTheDocument();
    await actor.click(screen.getByLabelText("Selecionar célula C2"));
    expect(screen.getByText(/excel_cell/i)).toBeInTheDocument();
    expect(screen.getAllByText(/15000/i).length).toBeGreaterThan(0);

    await actor.click(screen.getByRole("button", { name: /CSaldo Atual/i }));
    expect(screen.getByText(/excel_column/i)).toBeInTheDocument();
  });

  it("seleciona intervalo Excel por arrasto", () => {
    renderShell({ preview: excelPreview });

    fireEvent.mouseDown(screen.getByLabelText("Selecionar célula A1"));
    fireEvent.mouseEnter(screen.getByLabelText("Selecionar célula C2"));
    fireEvent.mouseUp(screen.getByLabelText("Selecionar célula C2"));

    expect(screen.getByText(/excel_range/i)).toBeInTheDocument();
    expect(screen.getAllByText(/A1/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/C2/i).length).toBeGreaterThan(0);
  });

  it("mostra estado de OCR obrigatório", () => {
    renderShell({ preview: { ...pdfPreview, requires_ocr: true, ocr_reason: "no_text_layer_detected", pages: [] }, state: "requires_ocr" });

    expect(screen.getByText("Este documento não possui texto extraível")).toBeInTheDocument();
  });

  it("mostra estados de loading, falha e preview ausente", () => {
    const { rerender } = render(
      <DocumentViewerShell
        document={documentRecord}
        preview={null}
        state="loading_preview"
        status="preview_processing"
        selection={null}
        onSelect={vi.fn()}
        onClearSelection={vi.fn()}
        onReload={vi.fn()}
        onRequestPreview={vi.fn()}
        onReprocessPreview={vi.fn()}
      />,
    );
    expect(screen.getByText("Carregando preview")).toBeInTheDocument();

    rerender(
      <DocumentViewerShell
        document={documentRecord}
        preview={null}
        state="preview_failed"
        status="preview_failed"
        error="arquivo corrompido"
        selection={null}
        onSelect={vi.fn()}
        onClearSelection={vi.fn()}
        onReload={vi.fn()}
        onRequestPreview={vi.fn()}
        onReprocessPreview={vi.fn()}
      />,
    );
    expect(screen.getByText("Não foi possível gerar preview deste documento")).toBeInTheDocument();

    rerender(
      <DocumentViewerShell
        document={documentRecord}
        preview={null}
        state="preview_missing"
        status="uploaded"
        selection={null}
        onSelect={vi.fn()}
        onClearSelection={vi.fn()}
        onReload={vi.fn()}
        onRequestPreview={vi.fn()}
        onReprocessPreview={vi.fn()}
      />,
    );
    expect(screen.getByText("Documento ainda não tem preview")).toBeInTheDocument();
  });
});

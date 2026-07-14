import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type React from "react";
import { describe, expect, it, vi } from "vitest";
import { TemplateBuilderPage } from "./TemplateBuilderPage";

const api = vi.hoisted(() => ({
  getBuilderState: vi.fn(),
  createField: vi.fn(),
  createAnnotationWithRule: vi.fn(),
  deleteAnnotation: vi.fn(),
  createSignal: vi.fn(),
  createVersion: vi.fn(),
  publishVersion: vi.fn(),
}));

vi.mock("../services/templateBuilderApi", () => ({
  templateBuilderApi: api,
}));

vi.mock("@/features/document-viewer/hooks/useDocumentPreview", () => ({
  useDocumentPreview: () => ({
    document: { documentId: "doc-1", originalFilename: "balancete.pdf", fileFormat: "PDF", status: "preview_ready" },
    preview: null,
    state: "preview_ready",
    status: "preview_ready",
    error: null,
    busyAction: null,
    reload: vi.fn(),
    requestPreview: vi.fn(),
    reprocessPreview: vi.fn(),
  }),
}));

vi.mock("@/features/document-viewer/components/DocumentViewerShell", () => ({
  DocumentViewerShell: ({ onSelect, sidePanel }: { onSelect: (value: unknown) => void; sidePanel?: React.ReactNode }) => (
    <div>
      <button
        type="button"
        onClick={() => onSelect({
          selection_type: "pdf_text_block",
          document_id: "doc-1",
          page_number: 1,
          text: "CNPJ: 00.000.000/0001-00",
          bbox: { x0: 10, y0: 20, x1: 180, y1: 40 },
          source: "preview",
        })}
      >
        Selecionar texto PDF
      </button>
      {sidePanel}
    </div>
  ),
}));

function mockState() {
  return {
    template: {
      templateId: "tpl-1",
      name: "Balancete PDF",
      categoryId: "cat-1",
      fileFormat: "PDF",
      structureType: "hierarchical",
      status: "active",
      activeVersionId: null,
    },
    activeVersion: null,
    draftVersion: { id: "ver-1", templateId: "tpl-1", versionNumber: 1, status: "draft", snapshot: {} },
    fields: [{
      id: "field-1",
      templateId: "tpl-1",
      fieldPath: "empresa.cnpj",
      label: "CNPJ",
      fieldType: "cnpj",
      isRequired: true,
      isRepeated: false,
      isObject: false,
      isArray: false,
      orderIndex: 0,
      status: "active",
    }],
    annotations: [],
    extractionRules: [],
    identificationSignals: [],
  };
}

describe("TemplateBuilderPage", () => {
  it("carrega template, cria campo e salva annotation com regra", async () => {
    const actor = userEvent.setup();
    api.getBuilderState.mockResolvedValue(mockState());
    api.createField.mockResolvedValue({ ...mockState().fields[0], id: "field-2", fieldPath: "contas[]", fieldType: "array" });
    api.createAnnotationWithRule.mockResolvedValue({ annotation: {}, extractionRule: { strategy: "find_near_label" }, suggestedConfig: {} });

    render(<TemplateBuilderPage templateId="tpl-1" documentId="doc-1" />);

    expect(await screen.findByText("Balancete PDF")).toBeInTheDocument();
    await actor.type(screen.getByLabelText("Campo/objeto"), "contas{[}{]}");
    await actor.click(screen.getByRole("button", { name: /Criar contas/i }));

    await waitFor(() => expect(api.createField).toHaveBeenCalledWith("tpl-1", expect.objectContaining({ fieldPath: "contas[]", isArray: true })));

    await actor.click(screen.getByText("Selecionar texto PDF"));
    await actor.click(screen.getByRole("button", { name: /Salvar annotation/i }));

    await waitFor(() => expect(api.createAnnotationWithRule).toHaveBeenCalledWith("tpl-1", expect.objectContaining({
      fieldId: "field-2",
      documentId: "doc-1",
      annotationType: "pdf_text_block",
      generateRule: true,
      ruleStrategy: "find_near_label",
    })));
  });
});

"use client";

import { useMemo } from "react";
import { AlertTriangle } from "lucide-react";
import { EmptyState } from "@/components/states/empty-state";
import type { PdfDocumentPreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";
import { PdfPageCanvas } from "./PdfPageCanvas";

export function PdfDocumentViewer({
  preview,
  zoom,
  currentPage,
  selection,
  evidences,
  onSelect,
}: {
  preview: PdfDocumentPreview;
  zoom: number;
  currentPage: number;
  selection: DocumentSelection | null;
  evidences: EvidenceHighlight[];
  onSelect: (selection: DocumentSelection) => void;
}) {
  const page = useMemo(
    () => preview.pages.find((item) => item.page_number === currentPage) || preview.pages[0],
    [currentPage, preview.pages],
  );

  if (preview.requires_ocr) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Este documento não possui texto extraível"
        description="Será necessário OCR em fase futura. Nesta fase o viewer não executa OCR nem cria seleção textual para PDFs sem camada de texto."
      />
    );
  }

  if (!page) {
    return (
      <EmptyState
        title="Preview PDF vazio"
        description="O backend retornou um preview pronto, mas sem páginas renderizáveis."
      />
    );
  }

  return (
    <div className="min-h-[620px] overflow-auto rounded-xl border border-border bg-white/[0.025] p-5">
      <PdfPageCanvas
        documentId={preview.document_id}
        page={page}
        zoom={zoom}
        selection={selection}
        evidences={evidences}
        onSelect={onSelect}
      />
    </div>
  );
}

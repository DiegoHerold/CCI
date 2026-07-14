"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, FileQuestion, Play } from "lucide-react";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Button } from "@/components/ui/button";
import type { DocumentRecord, ParsedDocumentPreview } from "../types/preview";
import { isExcelPreview, isPdfPreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";
import type { DocumentViewerLoadState } from "../hooks/useDocumentPreview";
import { ExcelDocumentViewer } from "./ExcelDocumentViewer";
import { PdfDocumentViewer } from "./PdfDocumentViewer";
import { SelectionPanel } from "./SelectionPanel";
import { ViewerToolbar } from "./ViewerToolbar";

function PreviewStateMessage({
  state,
  error,
  onRequestPreview,
  onReprocess,
  busy,
}: {
  state: DocumentViewerLoadState;
  error?: string | null;
  onRequestPreview: () => void;
  onReprocess: () => void;
  busy?: boolean;
}) {
  if (state === "loading_document") {
    return <LoadingState title="Carregando documento" description="Consultando os metadados pelo BFF." />;
  }
  if (state === "loading_preview") {
    return <LoadingState title="Carregando preview" description="Buscando o modelo estruturado no Document Service." />;
  }
  if (state === "preview_pending" || state === "preview_processing") {
    return (
      <EmptyState
        icon={Play}
        title="Preview ainda está em processamento"
        description="O documento já está registrado, mas o preview estruturado ainda não está pronto. Atualize a tela em instantes."
      />
    );
  }
  if (state === "preview_missing") {
    return (
      <EmptyState
        icon={FileQuestion}
        title="Documento ainda não tem preview"
        description="Solicite a geração do preview para habilitar seleção visual. Nenhum dado fictício será exibido."
        action={(
          <Button onClick={onRequestPreview} disabled={busy}>
            <Play aria-hidden="true" /> {busy ? "Solicitando" : "Gerar preview"}
          </Button>
        )}
      />
    );
  }
  if (state === "preview_failed") {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Não foi possível gerar preview deste documento"
        description={error || "O parser registrou uma falha para este arquivo."}
        action={(
          <Button variant="secondary" onClick={onReprocess} disabled={busy}>
            Reprocessar preview
          </Button>
        )}
      />
    );
  }
  if (state === "unsupported_format") {
    return (
      <EmptyState
        title="Formato ainda não suportado pelo viewer"
        description="Nesta fase o viewer renderiza preview estruturado de PDF e Excel."
      />
    );
  }
  if (state === "empty_preview") {
    return (
      <EmptyState
        title="Preview vazio"
        description="O backend informou preview pronto, mas sem elementos renderizáveis."
      />
    );
  }
  if (state === "error") {
    return <ErrorState title="Não foi possível abrir o documento" description={error || undefined} />;
  }
  return null;
}

export function DocumentViewerShell({
  document,
  preview,
  state,
  status,
  error,
  selection,
  evidences = [],
  busyAction,
  onSelect,
  onClearSelection,
  onReload,
  onRequestPreview,
  onReprocessPreview,
  sidePanel,
}: {
  document: DocumentRecord | null;
  preview: ParsedDocumentPreview | null;
  state: DocumentViewerLoadState;
  status?: string | null;
  error?: string | null;
  selection: DocumentSelection | null;
  evidences?: EvidenceHighlight[];
  busyAction?: "request" | "reprocess" | null;
  onSelect: (selection: DocumentSelection) => void;
  onClearSelection: () => void;
  onReload: () => void;
  onRequestPreview: () => void;
  onReprocessPreview: () => void;
  sidePanel?: React.ReactNode;
}) {
  const [zoom, setZoom] = useState(0.95);
  const [currentPage, setCurrentPage] = useState(1);
  const pageCount = isPdfPreview(preview) ? preview.pages.length : 0;
  const effectivePage = isPdfPreview(preview) && preview.pages.some((page) => page.page_number === currentPage)
    ? currentPage
    : isPdfPreview(preview)
      ? preview.pages[0]?.page_number ?? 1
      : currentPage;

  const viewer = useMemo(() => {
    if (state === "preview_ready" && isPdfPreview(preview)) {
      return (
        <PdfDocumentViewer
          preview={preview}
          zoom={zoom}
          currentPage={effectivePage}
          selection={selection}
          evidences={evidences}
          onSelect={onSelect}
        />
      );
    }
    if (state === "preview_ready" && isExcelPreview(preview)) {
      return (
        <ExcelDocumentViewer
          preview={preview}
          selection={selection}
          evidences={evidences}
          onSelect={onSelect}
        />
      );
    }
    if (state === "requires_ocr" && isPdfPreview(preview)) {
      return (
        <PdfDocumentViewer
          preview={preview}
          zoom={zoom}
          currentPage={effectivePage}
          selection={selection}
          evidences={evidences}
          onSelect={onSelect}
        />
      );
    }
    return (
      <PreviewStateMessage
        state={state}
        error={error}
        onRequestPreview={onRequestPreview}
        onReprocess={onReprocessPreview}
        busy={Boolean(busyAction)}
      />
    );
  }, [busyAction, effectivePage, error, evidences, onReprocessPreview, onRequestPreview, onSelect, preview, selection, state, zoom]);

  return (
    <div className="space-y-5">
      <ViewerToolbar
        document={document}
        status={status}
        zoom={isPdfPreview(preview) ? zoom : undefined}
        pageNumber={isPdfPreview(preview) ? effectivePage : undefined}
        pageCount={pageCount}
        onZoomIn={() => setZoom((value) => Math.min(1.6, Number((value + 0.1).toFixed(2))))}
        onZoomOut={() => setZoom((value) => Math.max(0.45, Number((value - 0.1).toFixed(2))))}
        onPageChange={setCurrentPage}
        onReload={onReload}
        onReprocess={document ? onReprocessPreview : undefined}
        reprocessing={busyAction === "reprocess"}
      />
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <main>{viewer}</main>
        <aside>
          {sidePanel ?? <SelectionPanel selection={selection} onClear={onClearSelection} />}
        </aside>
      </div>
    </div>
  );
}

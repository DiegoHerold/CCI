"use client";

import { DocumentViewerShell } from "./DocumentViewerShell";
import { useDocumentPreview } from "../hooks/useDocumentPreview";
import { useDocumentSelection } from "../hooks/useDocumentSelection";
import { useEvidenceHighlights } from "../hooks/useEvidenceHighlights";

export function DocumentViewerPage({ documentId }: { documentId: string }) {
  const previewState = useDocumentPreview(documentId);
  const { selection, setSelection, clearSelection } = useDocumentSelection();
  const evidences = useEvidenceHighlights();

  return (
    <DocumentViewerShell
      document={previewState.document}
      preview={previewState.preview}
      state={previewState.state}
      status={previewState.status}
      error={previewState.error}
      busyAction={previewState.busyAction}
      selection={selection}
      evidences={evidences}
      onSelect={setSelection}
      onClearSelection={clearSelection}
      onReload={() => void previewState.reload()}
      onRequestPreview={() => void previewState.requestPreview()}
      onReprocessPreview={() => void previewState.reprocessPreview()}
    />
  );
}

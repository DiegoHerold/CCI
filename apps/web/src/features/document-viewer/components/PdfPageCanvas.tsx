"use client";

import { useRef, useState } from "react";
import type { PdfPagePreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";
import { PdfEvidenceHighlightLayer } from "./EvidenceHighlightLayer";
import { PdfTextOverlay } from "./PdfTextOverlay";
import { buildPdfAreaSelection } from "../utils/selectionBuilders";
import { normalizePdfBox, scalePdfBox } from "../utils/pdfCoordinates";

export function PdfPageCanvas({
  documentId,
  page,
  zoom,
  selection,
  evidences,
  onSelect,
}: {
  documentId: string;
  page: PdfPagePreview;
  zoom: number;
  selection: DocumentSelection | null;
  evidences: EvidenceHighlight[];
  onSelect: (selection: DocumentSelection) => void;
}) {
  const scale = zoom;
  const ref = useRef<HTMLDivElement | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [dragEnd, setDragEnd] = useState<{ x: number; y: number } | null>(null);

  function pointerToPdf(event: React.PointerEvent<HTMLDivElement>) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: Math.max(0, Math.min(page.width, (event.clientX - rect.left) / scale)),
      y: Math.max(0, Math.min(page.height, (event.clientY - rect.top) / scale)),
    };
  }

  const previewBox = dragStart && dragEnd ? normalizePdfBox(dragStart, dragEnd) : null;

  return (
    <div className="mx-auto w-fit rounded-2xl border border-border-strong bg-black/30 p-4 shadow-2xl shadow-black/25">
      <div className="mb-3 flex items-center justify-between gap-3 text-xs text-muted">
        <span>Página {page.page_number}</span>
        <span>{page.lines.length} linhas | {page.text_blocks.length} blocos | {Math.round(page.width)} x {Math.round(page.height)} | rotacao {page.rotation} graus</span>
      </div>
      <div
        ref={ref}
        role="region"
        aria-label={`Página PDF ${page.page_number}`}
        className="relative overflow-hidden rounded-lg bg-white shadow-inner"
        style={{ width: page.width * scale, height: page.height * scale }}
        onPointerDown={(event) => {
          if (event.button !== 0) return;
          const point = pointerToPdf(event);
          setDragStart(point);
          setDragEnd(point);
          if (typeof ref.current?.setPointerCapture === "function") {
            ref.current.setPointerCapture(event.pointerId);
          }
        }}
        onPointerMove={(event) => {
          if (!dragStart) return;
          setDragEnd(pointerToPdf(event));
        }}
        onPointerUp={(event) => {
          if (!dragStart || !dragEnd) return;
          const bbox = normalizePdfBox(dragStart, dragEnd);
          setDragStart(null);
          setDragEnd(null);
          if (typeof ref.current?.releasePointerCapture === "function") {
            ref.current.releasePointerCapture(event.pointerId);
          }
          if (Math.abs(bbox.x1 - bbox.x0) > 4 && Math.abs(bbox.y1 - bbox.y0) > 4) {
            onSelect(buildPdfAreaSelection(documentId, page.page_number, bbox));
          }
        }}
      >
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(15,23,42,.018)_1px,transparent_1px),linear-gradient(180deg,rgba(15,23,42,.018)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <PdfEvidenceHighlightLayer pageNumber={page.page_number} scale={scale} evidences={evidences} />
        <PdfTextOverlay documentId={documentId} page={page} scale={scale} selection={selection} onSelect={onSelect} />
        {previewBox && (
          <div
            className="pointer-events-none absolute rounded-md border border-primary bg-primary/15"
            style={scalePdfBox(previewBox, scale)}
            data-testid="pdf-drag-preview"
          />
        )}
        {selection?.selection_type === "pdf_area" && selection.page_number === page.page_number && (
          <div
            className="pointer-events-none absolute rounded-md border-2 border-primary bg-primary/16 shadow-[0_0_28px_rgba(100,216,255,.20)]"
            style={scalePdfBox(selection.bbox, scale)}
            data-testid="pdf-area-selection"
          />
        )}
      </div>
    </div>
  );
}

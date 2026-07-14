"use client";

import Link from "next/link";
import { ArrowLeft, FileSearch, RefreshCw, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DocumentPreviewStatus, DocumentRecord } from "../types/preview";

function statusVariant(status?: string | null) {
  if (status === "preview_ready") return "success";
  if (status === "preview_failed") return "danger";
  if (status === "preview_pending" || status === "preview_processing") return "warning";
  return "neutral";
}

export function ViewerToolbar({
  document,
  status,
  zoom,
  pageNumber,
  pageCount,
  onZoomIn,
  onZoomOut,
  onPageChange,
  onReload,
  onReprocess,
  reprocessing,
}: {
  document: DocumentRecord | null;
  status?: DocumentPreviewStatus | string | null;
  zoom?: number;
  pageNumber?: number;
  pageCount?: number;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onPageChange?: (page: number) => void;
  onReload: () => void;
  onReprocess?: () => void;
  reprocessing?: boolean;
}) {
  return (
    <div className="sticky top-0 z-20 flex flex-col gap-3 rounded-xl border border-border bg-background/85 p-3 shadow-2xl shadow-black/20 backdrop-blur md:flex-row md:items-center md:justify-between">
      <div className="flex min-w-0 items-center gap-3">
        <Button asChild variant="ghost" size="sm">
          <Link href="/documents"><ArrowLeft aria-hidden="true" /> Voltar</Link>
        </Button>
        <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-primary/15 bg-primary/8 text-primary">
          <FileSearch className="size-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white">{document?.originalFilename || "Documento"}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge variant={statusVariant(status)}>{status || "carregando"}</Badge>
            {document?.fileFormat && <Badge>{document.fileFormat}</Badge>}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {typeof zoom === "number" && (
          <div className="flex items-center gap-1 rounded-lg border border-border bg-white/[0.035] p-1">
            <Button variant="ghost" size="sm" onClick={onZoomOut} aria-label="Diminuir zoom"><ZoomOut /></Button>
            <span className="min-w-14 text-center text-xs font-semibold text-muted-strong">{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={onZoomIn} aria-label="Aumentar zoom"><ZoomIn /></Button>
          </div>
        )}
        {typeof pageCount === "number" && pageCount > 0 && (
          <label className="flex items-center gap-2 rounded-lg border border-border bg-white/[0.035] px-3 py-2 text-xs text-muted">
            Página
            <select
              className="rounded-md border border-border bg-background px-2 py-1 text-foreground"
              value={pageNumber}
              onChange={(event) => onPageChange?.(Number(event.target.value))}
            >
              {Array.from({ length: pageCount }, (_, index) => (
                <option key={index + 1} value={index + 1}>{index + 1}</option>
              ))}
            </select>
            de {pageCount}
          </label>
        )}
        <Button variant="secondary" size="sm" onClick={onReload}>
          <RefreshCw aria-hidden="true" /> Atualizar
        </Button>
        {onReprocess && (
          <Button variant="secondary" size="sm" onClick={onReprocess} disabled={reprocessing}>
            <RotateCcw aria-hidden="true" /> {reprocessing ? "Reprocessando" : "Reprocessar"}
          </Button>
        )}
      </div>
    </div>
  );
}

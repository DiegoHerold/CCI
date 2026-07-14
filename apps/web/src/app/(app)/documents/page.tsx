"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Eye, FileStack, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { ServiceUnavailableState } from "@/components/states/service-unavailable-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RequirePermission } from "@/features/auth/require-permission";
import { documentPreviewApi } from "@/features/document-viewer/services/documentPreviewApi";
import type { DocumentRecord } from "@/features/document-viewer/types/preview";
import { classifyApiError } from "@/lib/api/error-utils";

type PageStatus = "loading" | "ready" | "error" | "unavailable";

function statusVariant(status: string) {
  if (status === "preview_ready") return "success";
  if (status === "preview_failed") return "danger";
  if (status === "preview_pending" || status === "preview_processing") return "warning";
  return "neutral";
}

export default function DocumentsPage() {
  return (
    <RequirePermission permission="conferences:read">
      <DocumentsContent />
    </RequirePermission>
  );
}

function DocumentsContent() {
  const [items, setItems] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<PageStatus>("loading");

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const response = await documentPreviewApi.list({ limit: 50 });
      setItems(response.items ?? []);
      setStatus("ready");
    } catch (error) {
      setItems([]);
      setStatus(classifyApiError(error) === "SERVICE_UNAVAILABLE" ? "unavailable" : "error");
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Data Plane"
        title="Documentos"
        description="Documentos registrados no Document Service. Abra um item para visualizar o preview estruturado e preparar seleções reutilizáveis."
        action={(
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" /> Atualizar
          </Button>
        )}
      />

      {status === "loading" && <LoadingState title="Carregando documentos" description="Consultando o Document Service pelo BFF." />}
      {status === "error" && <ErrorState onRetry={() => void load()} />}
      {status === "unavailable" && (
        <ServiceUnavailableState
          description="A tela de documentos está pronta, mas o endpoint GET /documents ainda não respondeu pelo BFF."
          onRetry={() => void load()}
        />
      )}
      {status === "ready" && !items.length && (
        <EmptyState
          icon={FileStack}
          title="Documentos ainda não importados"
          description="Quando o Document Service registrar arquivos reais, eles aparecerão aqui. Nenhum documento fictício é exibido."
        />
      )}
      {status === "ready" && Boolean(items.length) && (
        <div className="grid gap-3 lg:grid-cols-2">
          {items.map((document) => (
            <ThemeSurface key={document.documentId} className="p-5 transition hover:-translate-y-0.5 hover:border-border-strong">
              <div className="flex items-start justify-between gap-4">
                <span className="grid size-11 place-items-center rounded-xl border border-primary/15 bg-primary/8 text-primary">
                  <FileStack className="size-5" aria-hidden="true" />
                </span>
                <Badge variant={statusVariant(document.status)}>{document.status}</Badge>
              </div>
              <h2 className="mt-5 line-clamp-2 font-semibold text-white">{document.originalFilename}</h2>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted">
                <Badge>{document.fileFormat}</Badge>
                <span className="font-mono">{document.documentId}</span>
              </div>
              <div className="mt-5 flex items-center justify-between border-t border-border pt-4 text-xs text-muted">
                <span>{document.sizeBytes ? `${Math.round(document.sizeBytes / 1024)} KB` : "Tamanho não informado"}</span>
                <Button asChild size="sm">
                  <Link href={`/documents/${document.documentId}`}>
                    <Eye aria-hidden="true" /> Abrir viewer
                  </Link>
                </Button>
              </div>
            </ThemeSurface>
          ))}
        </div>
      )}
    </div>
  );
}

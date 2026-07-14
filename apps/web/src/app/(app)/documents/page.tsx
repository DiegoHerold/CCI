"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Eye, FileStack, Plus, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { ServiceUnavailableState } from "@/components/states/service-unavailable-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RequirePermission } from "@/features/auth/require-permission";
import { useOperationalContext } from "@/features/context/operational-context-provider";
import { documentFlowApi, type DocumentFlowState } from "@/features/document-intake/services/documentFlowApi";
import { documentPreviewApi } from "@/features/document-viewer/services/documentPreviewApi";
import type { DocumentRecord } from "@/features/document-viewer/types/preview";
import { clientContextApi } from "@/lib/api/client-context-api";
import { classifyApiError } from "@/lib/api/error-utils";
import { ApiError } from "@/lib/api/http-client";

type PageStatus = "loading" | "ready" | "error" | "unavailable";

function statusVariant(status: string) {
  if (status === "completed" || status === "completed_with_warnings" || status === "matched" || status === "confirmed") return "success";
  if (status === "requires_review" || status === "ambiguous") return "warning";
  if (status === "failed" || status === "not_found") return "danger";
  if (status === "preview_ready") return "success";
  if (status === "preview_failed") return "danger";
  if (status === "preview_pending" || status === "preview_processing") return "warning";
  return "neutral";
}

function DocumentFlowBadges({ documentId }: { documentId: string }) {
  const [flow, setFlow] = useState<DocumentFlowState | null>(null);

  useEffect(() => {
    let active = true;
    documentFlowApi.getFlowState(documentId)
      .then((state) => {
        if (active) setFlow(state);
      })
      .catch(() => {
        if (active) setFlow(null);
      });
    return () => {
      active = false;
    };
  }, [documentId]);

  if (!flow) return <p className="mt-4 text-xs text-muted">Fluxo ainda nao carregado.</p>;

  return (
    <div className="mt-4 grid gap-2 text-xs sm:grid-cols-2">
      <Badge variant={statusVariant(flow.preview.status)}>Leitura: {flow.preview.status}</Badge>
      <Badge variant={statusVariant(flow.template_matching.status)}>Template: {flow.template_matching.status}</Badge>
      <Badge variant={statusVariant(flow.extraction.status)}>Extracao: {flow.extraction.status}</Badge>
      <Badge variant={statusVariant(flow.normalization.status)}>Normalizacao: {flow.normalization.status}</Badge>
      <span className="sm:col-span-2 text-muted">Proxima acao: {flow.next_action.label}</span>
    </div>
  );
}

export default function DocumentsPage() {
  return (
    <RequirePermission permission="conferences:read">
      <DocumentsContent />
    </RequirePermission>
  );
}

function DocumentsContent() {
  const { data, selectedClient, selectedClientId } = useOperationalContext();
  const [items, setItems] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<PageStatus>("loading");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const response = await documentPreviewApi.list({ limit: 50, clientId: selectedClientId ?? undefined });
      setItems(response.items ?? []);
      setStatus("ready");
    } catch (error) {
      setItems([]);
      setStatus(classifyApiError(error) === "SERVICE_UNAVAILABLE" ? "unavailable" : "error");
    }
  }, [selectedClientId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  async function handleUpload(file: File | null) {
    setUploadError(null);
    setUploadSuccess(null);
    if (!file) return;
    if (!selectedClientId) {
      setUploadError("Selecione um cliente no topo antes de enviar arquivos.");
      return;
    }
    setUploading(true);
    try {
      const competence = await clientContextApi.ensureCurrentCompetency(selectedClientId, data?.currentCompetence.period);
      const uploaded = await documentPreviewApi.upload({ file, clientId: selectedClientId, competenceId: competence.id });
      if (uploaded.documentId) {
        await documentPreviewApi.requestPreview(uploaded.documentId).catch(() => null);
      }
      setUploadSuccess(`Arquivo "${file.name}" enviado para ${selectedClient?.tradeName || selectedClient?.name || "o cliente selecionado"} e preview solicitado.`);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await load();
    } catch (error) {
      setUploadError(
        error instanceof ApiError
          ? error.message
          : "Nao foi possivel enviar o arquivo. Confira cliente, competencia e permissao.",
      );
    } finally {
      setUploading(false);
    }
  }

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

      <ThemeSurface className="grid gap-4 p-5 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="grid size-10 place-items-center rounded-lg border border-primary/15 bg-primary/8 text-primary">
              <Plus aria-hidden="true" />
            </span>
            <div>
              <h2 className="font-semibold text-white">Enviar arquivos</h2>
              <p className="text-sm text-muted">
                {selectedClient
                  ? `Cliente: ${selectedClient.tradeName || selectedClient.name} | Competencia: ${data?.currentCompetence.period || "atual"}`
                  : "Selecione um cliente no topo para habilitar o upload."}
              </p>
            </div>
          </div>
          {uploadError && <p className="text-sm text-danger">{uploadError}</p>}
          {uploadSuccess && <p className="text-sm text-success">{uploadSuccess}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.xlsx,.xls,.csv,.txt,.docx,.xml,.zip,image/*"
            disabled={uploading || !selectedClientId}
            onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
            className="max-w-full rounded-md border border-border-strong bg-black/20 px-3 py-2 text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-primary-foreground disabled:opacity-50"
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading || !selectedClientId}>
            <FileStack aria-hidden="true" /> {uploading ? "Enviando" : "Selecionar arquivo"}
          </Button>
        </div>
      </ThemeSurface>

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
              <DocumentFlowBadges documentId={document.documentId} />
              <div className="mt-5 flex items-center justify-between border-t border-border pt-4 text-xs text-muted">
                <span>{document.sizeBytes ? `${Math.round(document.sizeBytes / 1024)} KB` : "Tamanho não informado"}</span>
                <Button asChild size="sm">
                  <Link href={`/documents/${document.documentId}`}>
                    <Eye aria-hidden="true" /> Abrir fluxo
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

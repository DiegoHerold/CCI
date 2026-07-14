"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, FileSearch, Play, RefreshCw, Workflow } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DocumentViewerPage } from "@/features/document-viewer/components/DocumentViewerPage";
import { ApiError } from "@/lib/api/http-client";
import { documentFlowApi, type DocumentFlowState } from "../services/documentFlowApi";

function badgeVariant(status?: string | null) {
  if (!status || status === "not_started") return "neutral";
  if (["completed", "completed_with_warnings", "preview_ready", "matched", "confirmed"].includes(status)) return "success";
  if (["requires_review", "ambiguous", "preview_pending", "preview_processing"].includes(status)) return "warning";
  if (["failed", "not_found", "preview_failed"].includes(status)) return "danger";
  return "info";
}

function FlowStep({ label, status }: { label: string; status?: string | null }) {
  return (
    <div className="flex min-w-[150px] items-center gap-2 rounded-md border border-border bg-black/10 px-3 py-2">
      <CheckCircle2 className="size-4 text-primary" aria-hidden="true" />
      <div>
        <p className="text-xs font-medium text-white">{label}</p>
        <Badge variant={badgeVariant(status)}>{status || "not_started"}</Badge>
      </div>
    </div>
  );
}

export function DocumentFlowPage({ documentId }: { documentId: string }) {
  const [flow, setFlow] = useState<DocumentFlowState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setFlow(await documentFlowApi.getFlowState(documentId));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel carregar o fluxo do documento.");
    }
  }, [documentId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  const run = async (action: string) => {
    if (!flow) return;
    setBusy(action);
    setError(null);
    try {
      if (action === "run_template_match") await documentFlowApi.runTemplateMatch(documentId);
      if (action === "confirm_template" && flow.template.template_id && flow.template.template_version_id) {
        await documentFlowApi.confirmTemplate(documentId, flow.template.template_id, flow.template.template_version_id);
      }
      if (action === "start_extraction") await documentFlowApi.startExtraction(documentId);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "A acao nao foi concluida.");
    } finally {
      setBusy(null);
    }
  };

  if (!flow && !error) return <LoadingState title="Carregando fluxo" description="Consultando documentos, template matching e extracao pelo BFF." />;
  if (error && !flow) return <ErrorState title="Nao foi possivel abrir o fluxo" description={error} onRetry={() => void load()} />;

  const nextAction = flow!.next_action;
  const filename = flow!.document.filename || documentId;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Fluxo guiado"
        title={filename}
        description="Acompanhe o caminho do documento ate as variaveis normalizadas, sem precisar navegar pelos detalhes tecnicos internos."
        action={(
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" /> Atualizar
          </Button>
        )}
      />

      {error && <ErrorState title="Acao nao concluida" description={error} onRetry={() => setError(null)} />}

      <ThemeSurface className="space-y-4 p-4">
        <div className="flex flex-wrap gap-3">
          <FlowStep label="Documento enviado" status={flow!.document.status} />
          <FlowStep label="Documento lido" status={flow!.preview.status} />
          <FlowStep label="Template" status={flow!.template_matching.status} />
          <FlowStep label="Extracao" status={flow!.extraction.status} />
          <FlowStep label="Variaveis" status={flow!.result.status || flow!.normalization.status} />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
          <div>
            <p className="text-sm font-semibold text-white">Proxima acao</p>
            <p className="text-sm text-muted">{nextAction.label}</p>
          </div>
          {nextAction.type === "request_preview" && (
            <Button asChild>
              <Link href={`/documents/${documentId}`}>
                <FileSearch aria-hidden="true" /> Ler documento
              </Link>
            </Button>
          )}
          {["run_template_match", "confirm_template", "start_extraction"].includes(nextAction.type) && (
            <Button onClick={() => void run(nextAction.type)} disabled={Boolean(busy)}>
              <Play aria-hidden="true" /> {busy ? "Executando" : nextAction.label}
            </Button>
          )}
          {["create_template", "choose_template"].includes(nextAction.type) && (
            <Button asChild>
              <Link href={`/documents/${documentId}/template-builder`}>
                <Workflow aria-hidden="true" /> {nextAction.label}
              </Link>
            </Button>
          )}
          {["review_variables", "view_result"].includes(nextAction.type) && (
            <Button asChild>
              <Link href={`/documents/${documentId}/extraction`}>
                <CheckCircle2 aria-hidden="true" /> {nextAction.label}
              </Link>
            </Button>
          )}
        </div>
      </ThemeSurface>

      <DocumentViewerPage documentId={documentId} />
    </div>
  );
}

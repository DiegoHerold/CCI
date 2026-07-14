"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Eye, RefreshCw, Search, ShieldCheck, SlidersHorizontal, X } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/http-client";
import {
  extractionReviewApi,
  type ExtractedFieldValue,
  type ExtractedObject,
  type ExtractionEvidence,
  type ExtractionResultSummary,
} from "../services/extractionReviewApi";

function statusVariant(status: string) {
  if (["normalized", "approved", "corrected", "completed", "completed_with_warnings"].includes(status)) return "success";
  if (["requires_review", "low_confidence", "evidence_missing", "ambiguous", "normalization_failed", "not_found"].includes(status)) return "warning";
  if (["rejected", "failed"].includes(status)) return "danger";
  return "neutral";
}

function objectName(path: string) {
  if (path.includes("[]")) return path.split("[]")[0] || path;
  return path.split(".")[0] || "geral";
}

function valueText(field: ExtractedFieldValue) {
  return field.displayValue || field.normalizedValue || String(field.rawValue ?? "-");
}

export function ExtractionReviewPage({ documentId }: { documentId: string }) {
  const [result, setResult] = useState<ExtractionResultSummary | null>(null);
  const [fields, setFields] = useState<ExtractedFieldValue[]>([]);
  const [objects, setObjects] = useState<ExtractedObject[]>([]);
  const [selectedField, setSelectedField] = useState<ExtractedFieldValue | null>(null);
  const [evidence, setEvidence] = useState<ExtractionEvidence[]>([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [importantOnly, setImportantOnly] = useState(false);
  const [lowConfidenceOnly, setLowConfidenceOnly] = useState(false);
  const [missingEvidenceOnly, setMissingEvidenceOnly] = useState(false);
  const [correctionValue, setCorrectionValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const nextResult = await extractionReviewApi.latestResult(documentId);
      const [nextFields, nextObjects] = await Promise.all([
        extractionReviewApi.listFields(nextResult.extractionResultId),
        extractionReviewApi.listObjects(nextResult.extractionResultId),
      ]);
      setResult(nextResult);
      setFields(nextFields.items ?? []);
      setObjects(nextObjects.items ?? []);
      setSelectedField(null);
      setEvidence([]);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel carregar o resultado da extracao.");
    }
  }, [documentId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  const filteredFields = useMemo(() => {
    const search = query.trim().toLowerCase();
    return fields
      .filter((field) => !statusFilter || field.status === statusFilter)
      .filter((field) => !typeFilter || field.fieldType === typeFilter)
      .filter((field) => !importantOnly || Boolean(field.metadataJson?.important))
      .filter((field) => !lowConfidenceOnly || field.confidence < 0.75 || field.status === "low_confidence")
      .filter((field) => !missingEvidenceOnly || !field.evidenceId || field.status === "evidence_missing")
      .filter((field) => {
        if (!search) return true;
        return [field.fieldPath, field.fieldType, field.status, valueText(field), String(field.rawValue ?? "")]
          .some((value) => value.toLowerCase().includes(search));
      })
      .sort((a, b) => {
        const pendingA = statusVariant(a.status) === "warning" ? 0 : 1;
        const pendingB = statusVariant(b.status) === "warning" ? 0 : 1;
        return pendingA - pendingB || a.confidence - b.confidence || a.fieldPath.localeCompare(b.fieldPath);
      });
  }, [fields, importantOnly, lowConfidenceOnly, missingEvidenceOnly, query, statusFilter, typeFilter]);

  const importantFields = filteredFields.filter((field) => Boolean(field.metadataJson?.important)).slice(0, 8);
  const fieldTypes = Array.from(new Set(fields.map((field) => field.fieldType))).sort();
  const statuses = Array.from(new Set(fields.map((field) => field.status))).sort();
  const groups = Array.from(new Set(filteredFields.map((field) => objectName(field.fieldPath)))).sort();

  const loadEvidence = async (field: ExtractedFieldValue) => {
    setSelectedField(field);
    setCorrectionValue(String(field.rawValue ?? ""));
    setBusy("evidence");
    try {
      const response = await extractionReviewApi.listEvidence(field.fieldValueId);
      setEvidence(response.items ?? []);
    } catch {
      setEvidence([]);
    } finally {
      setBusy(null);
    }
  };

  const reviewAction = async (action: "approve" | "reject" | "correct") => {
    if (!selectedField) return;
    setBusy(action);
    setError(null);
    try {
      if (action === "approve") await extractionReviewApi.approveField(selectedField.fieldValueId, "Revisado no frontend");
      if (action === "reject") await extractionReviewApi.rejectField(selectedField.fieldValueId, "Rejeitado no frontend");
      if (action === "correct") await extractionReviewApi.correctField(selectedField.fieldValueId, correctionValue, "Corrigido no frontend");
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel salvar a revisao.");
    } finally {
      setBusy(null);
    }
  };

  const approveResult = async () => {
    if (!result) return;
    setBusy("approve-result");
    try {
      await extractionReviewApi.approveResult(result.extractionResultId, "Resultado aprovado no frontend");
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel aprovar o resultado.");
    } finally {
      setBusy(null);
    }
  };

  if (!result && !error) return <LoadingState title="Carregando variaveis" description="Consultando resultado normalizado pelo BFF." />;
  if (error && !result) return <ErrorState title="Nao ha resultado de extracao" description={error} onRetry={() => void load()} />;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Review de variaveis"
        title="Variaveis extraidas"
        description="Revise valores normalizados, evidencias e pendencias antes das regras contabeis consumirem os dados."
        action={(
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" /> Atualizar
          </Button>
        )}
      />

      {error && <ErrorState title="Acao nao concluida" description={error} onRetry={() => setError(null)} />}

      <div className="grid gap-3 lg:grid-cols-5">
        <ThemeSurface className="p-4"><p className="text-xs text-muted">Variaveis</p><p className="text-2xl font-semibold text-white">{result!.fieldCount}</p></ThemeSurface>
        <ThemeSurface className="p-4"><p className="text-xs text-muted">Normalizadas</p><p className="text-2xl font-semibold text-white">{result!.normalizedCount}</p></ThemeSurface>
        <ThemeSurface className="p-4"><p className="text-xs text-muted">Pendencias</p><p className="text-2xl font-semibold text-white">{result!.requiresReviewCount}</p></ThemeSurface>
        <ThemeSurface className="p-4"><p className="text-xs text-muted">Template</p><p className="truncate text-sm font-semibold text-white">{result!.templateId}</p></ThemeSurface>
        <ThemeSurface className="p-4"><p className="text-xs text-muted">Status</p><Badge variant={statusVariant(result!.status)}>{result!.status}</Badge></ThemeSurface>
      </div>

      <ThemeSurface className="space-y-3 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Search className="size-4" aria-hidden="true" /> Busca e filtros
        </div>
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_180px_auto_auto_auto]">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por nome, field_path, valor ou status" />
          <select className="h-11 rounded-md border border-border-strong bg-black/20 px-3 text-sm text-foreground" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">Todos os status</option>
            {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
          <select className="h-11 rounded-md border border-border-strong bg-black/20 px-3 text-sm text-foreground" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
            <option value="">Todos os tipos</option>
            {fieldTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          <Button variant={importantOnly ? "default" : "secondary"} onClick={() => setImportantOnly((value) => !value)}><SlidersHorizontal aria-hidden="true" /> Importantes</Button>
          <Button variant={lowConfidenceOnly ? "default" : "secondary"} onClick={() => setLowConfidenceOnly((value) => !value)}>Baixa confianca</Button>
          <Button variant={missingEvidenceOnly ? "default" : "secondary"} onClick={() => setMissingEvidenceOnly((value) => !value)}>Sem evidencia</Button>
        </div>
      </ThemeSurface>

      {importantFields.length > 0 && (
        <ThemeSurface className="space-y-3 p-4">
          <h2 className="font-semibold text-white">Variaveis importantes</h2>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {importantFields.map((field) => (
              <button key={field.fieldValueId} className="rounded-md border border-border bg-black/10 p-3 text-left" onClick={() => void loadEvidence(field)}>
                <p className="text-sm font-semibold text-white">{field.metadataJson?.label as string || field.fieldPath}</p>
                <p className="mt-1 truncate text-sm text-muted">{valueText(field)}</p>
                <Badge variant={statusVariant(field.status)}>{field.status}</Badge>
              </button>
            ))}
          </div>
        </ThemeSurface>
      )}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          {groups.map((group) => (
            <ThemeSurface key={group} className="overflow-hidden p-0">
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <h2 className="font-semibold text-white">{group}</h2>
                <Badge>{objects.filter((object) => object.fieldPath.startsWith(group)).length || "campos"}</Badge>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="border-b border-border text-xs text-muted">
                    <tr>
                      <th className="px-4 py-3">Campo</th>
                      <th className="px-4 py-3">Valor</th>
                      <th className="px-4 py-3">Tipo</th>
                      <th className="px-4 py-3">Confianca</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Evidencia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFields.filter((field) => objectName(field.fieldPath) === group).map((field) => (
                      <tr key={field.fieldValueId} className="border-b border-border/60">
                        <td className="px-4 py-3 font-mono text-xs text-muted">{field.fieldPath}</td>
                        <td className="px-4 py-3 text-white">{valueText(field)}</td>
                        <td className="px-4 py-3"><Badge>{field.fieldType}</Badge></td>
                        <td className="px-4 py-3">{Math.round(field.confidence * 100)}%</td>
                        <td className="px-4 py-3"><Badge variant={statusVariant(field.status)}>{field.status}</Badge></td>
                        <td className="px-4 py-3">
                          <Button size="sm" variant="secondary" onClick={() => void loadEvidence(field)}>
                            <Eye aria-hidden="true" /> Abrir
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ThemeSurface>
          ))}
          {!filteredFields.length && <EmptyState title="Nenhuma variavel encontrada" description="Ajuste os filtros ou reexecute a extracao." />}
        </div>

        <ThemeSurface className="h-fit space-y-4 p-4">
          <h2 className="font-semibold text-white">Evidencia e revisao</h2>
          {!selectedField && <p className="text-sm text-muted">Selecione uma variavel para ver origem, regra e acoes de revisao.</p>}
          {selectedField && (
            <>
              <div className="space-y-2">
                <p className="font-mono text-xs text-muted">{selectedField.fieldPath}</p>
                <p className="text-sm text-white">Bruto: {String(selectedField.rawValue ?? "-")}</p>
                <p className="text-sm text-white">Normalizado: {valueText(selectedField)}</p>
                <Badge variant={statusVariant(selectedField.status)}>{selectedField.status}</Badge>
              </div>
              {busy === "evidence" && <p className="text-sm text-muted">Carregando evidencia...</p>}
              {evidence.map((item) => (
                <div key={item.evidenceId} className="rounded-md border border-border bg-black/10 p-3 text-sm text-muted">
                  <p>Tipo: {item.evidenceType}</p>
                  {item.pageNumber && <p>Pagina: {item.pageNumber}</p>}
                  {item.sheetName && <p>Aba: {item.sheetName}</p>}
                  {item.cellRange && <p>Celula/range: {item.cellRange}</p>}
                  <p>Regra: {item.ruleStrategy || "-"}</p>
                  <p>Origem: {item.sourceText || String(item.sourceValue ?? "-")}</p>
                </div>
              ))}
              {!evidence.length && busy !== "evidence" && <p className="text-sm text-muted">Sem evidencia vinculada para este campo.</p>}
              <Input value={correctionValue} onChange={(event) => setCorrectionValue(event.target.value)} placeholder="Valor corrigido" />
              <div className="grid gap-2">
                <Button onClick={() => void reviewAction("correct")} disabled={Boolean(busy)}><CheckCircle2 aria-hidden="true" /> Corrigir</Button>
                <Button variant="secondary" onClick={() => void reviewAction("approve")} disabled={Boolean(busy)}><ShieldCheck aria-hidden="true" /> Aprovar variavel</Button>
                <Button variant="danger" onClick={() => void reviewAction("reject")} disabled={Boolean(busy)}><X aria-hidden="true" /> Rejeitar variavel</Button>
              </div>
            </>
          )}
          <div className="border-t border-border pt-4">
            <Button className="w-full" onClick={() => void approveResult()} disabled={Boolean(busy) || !result}>
              <ShieldCheck aria-hidden="true" /> Aprovar resultado completo
            </Button>
          </div>
        </ThemeSurface>
      </div>
    </div>
  );
}

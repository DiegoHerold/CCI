"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, CheckCircle2, FileCheck2, RefreshCw, Workflow } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/http-client";
import { templateBuilderApi } from "../services/templateBuilderApi";
import type { TemplateCategory, TemplateSuggestionResponse } from "../types/templateBuilder";

export function GuidedTemplateBuilderFromDocument({ documentId }: { documentId: string }) {
  const [suggestions, setSuggestions] = useState<TemplateSuggestionResponse | null>(null);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [savedTemplateId, setSavedTemplateId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [nextSuggestions, categoryResponse] = await Promise.all([
        templateBuilderApi.suggestFromDocument(documentId),
        templateBuilderApi.listCategories(),
      ]);
      setSuggestions(nextSuggestions);
      setCategories(categoryResponse.items ?? []);
      setSelectedCategoryId((current) => current || categoryResponse.items?.[0]?.id || "");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel gerar sugestoes para este documento.");
    }
  }, [documentId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  const suggestedRulesByPath = useMemo(() => {
    const map = new Map<string, TemplateSuggestionResponse["suggestedRules"][number]>();
    for (const rule of suggestions?.suggestedRules ?? []) map.set(rule.fieldPath, rule);
    return map;
  }, [suggestions]);

  const saveAndPublish = async () => {
    if (!suggestions || !selectedCategoryId) return;
    setBusy("save");
    setError(null);
    try {
      const template = await templateBuilderApi.createTemplate({
        name: suggestions.suggestedTemplate.name,
        description: `Criado a partir do documento ${documentId}`,
        categoryId: selectedCategoryId,
        fileFormat: suggestions.suggestedTemplate.fileFormat as any,
        structureType: suggestions.suggestedTemplate.structureType as any,
      });
      const createdFieldsByPath = new Map<string, string>();
      for (const field of suggestions.suggestedFields) {
        const created = await templateBuilderApi.createField(template.templateId, {
          fieldPath: field.fieldPath,
          label: field.label,
          fieldType: field.fieldType,
          isRequired: field.required,
          important: field.important,
          isRepeated: field.fieldPath.includes("[]") || field.fieldType === "array" || field.fieldType === "table",
          isArray: field.fieldType === "array" || field.fieldPath.endsWith("[]"),
          isObject: field.fieldType === "object",
        });
        createdFieldsByPath.set(field.fieldPath, created.id);
      }
      for (const rule of suggestions.suggestedRules) {
        const fieldId = createdFieldsByPath.get(rule.fieldPath);
        if (!fieldId) continue;
        await templateBuilderApi.createExtractionRule(template.templateId, {
          fieldId,
          strategy: rule.strategy,
          config: rule.config,
          confidenceHint: rule.confidence,
        });
      }
      const firstSignal = suggestions.suggestedFields.find((field) => field.rawSample);
      if (firstSignal?.rawSample) {
        await templateBuilderApi.createSignal(template.templateId, {
          signalType: "contains_text",
          value: String(firstSignal.rawSample),
          weight: 10,
          required: false,
          negative: false,
        });
      }
      const version = await templateBuilderApi.createVersion(template.templateId);
      await templateBuilderApi.publishVersion(template.templateId, version.id);
      setSavedTemplateId(template.templateId);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel salvar/publicar o template.");
    } finally {
      setBusy(null);
    }
  };

  if (!suggestions && !error) return <LoadingState title="Analisando preview" description="Buscando padroes, campos provaveis e regras tecnicas." />;
  if (error && !suggestions) return <ErrorState title="Nao foi possivel abrir o builder guiado" description={error} onRetry={() => void load()} />;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Template Builder guiado"
        title={suggestions?.suggestedTemplate.name || "Novo template"}
        description="Revise sugestoes do sistema, salve o template e volte ao documento para reexecutar a identificacao."
        action={(
          <Button asChild variant="secondary">
            <Link href={`/documents/${documentId}`}>
              <ArrowLeft aria-hidden="true" /> Voltar ao documento
            </Link>
          </Button>
        )}
      />

      {error && <ErrorState title="Acao nao concluida" description={error} onRetry={() => setError(null)} />}

      {savedTemplateId && (
        <ThemeSurface className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="font-semibold text-white">Template salvo e publicado</p>
            <p className="text-sm text-muted">Volte ao documento e rode a identificacao novamente.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="secondary">
              <Link href={`/templates/${savedTemplateId}/builder?documentId=${documentId}`}>
                <Workflow aria-hidden="true" /> Ajustar visualmente
              </Link>
            </Button>
            <Button asChild>
              <Link href={`/documents/${documentId}`}>
                <CheckCircle2 aria-hidden="true" /> Voltar e reprocessar
              </Link>
            </Button>
          </div>
        </ThemeSurface>
      )}

      <ThemeSurface className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <Badge variant="info">{suggestions!.suggestedTemplate.fileFormat}</Badge>
            <Badge>{suggestions!.suggestedTemplate.structureType}</Badge>
            <Badge>{suggestions!.suggestedTemplate.category}</Badge>
          </div>
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" /> Atualizar sugestoes
          </Button>
        </div>
        <label className="block text-sm text-muted">
          Categoria
          <select
            className="mt-2 h-11 w-full rounded-md border border-border-strong bg-black/20 px-3 text-sm text-foreground"
            value={selectedCategoryId}
            onChange={(event) => setSelectedCategoryId(event.target.value)}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
      </ThemeSurface>

      {!suggestions!.suggestedFields.length && (
        <EmptyState title="Nenhuma sugestao forte" description="O preview nao revelou campos comuns suficientes. Abra o builder visual para mapear manualmente." />
      )}

      <div className="grid gap-3 lg:grid-cols-2">
        {suggestions!.suggestedFields.map((field) => {
          const rule = suggestedRulesByPath.get(field.fieldPath);
          return (
            <ThemeSurface key={field.fieldPath} className="space-y-3 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-white">{field.label}</p>
                  <p className="font-mono text-xs text-muted">{field.fieldPath}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge>{field.fieldType}</Badge>
                  {field.important && <Badge variant="warning">importante</Badge>}
                  {field.required && <Badge variant="info">obrigatorio</Badge>}
                </div>
              </div>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <span className="text-muted">Bruto: {String(field.rawSample ?? "-")}</span>
                <span className="text-muted">Normalizado: {field.displayValue || field.normalizedPreview || "-"}</span>
                <span className="text-muted">Confianca: {Math.round(field.confidence * 100)}%</span>
                <span className="text-muted">Regra: {rule?.strategy || "a definir"}</span>
              </div>
            </ThemeSurface>
          );
        })}
      </div>

      <ThemeSurface className="flex flex-wrap items-center justify-between gap-3 p-4">
        <p className="text-sm text-muted">Salvar cria campos, regras tecnicas sugeridas, um sinal de identificacao e publica uma versao inicial do template.</p>
        <Button onClick={() => void saveAndPublish()} disabled={Boolean(busy) || !selectedCategoryId || Boolean(savedTemplateId)}>
          <FileCheck2 aria-hidden="true" /> {busy ? "Salvando" : "Salvar e publicar template"}
        </Button>
      </ThemeSurface>
    </div>
  );
}

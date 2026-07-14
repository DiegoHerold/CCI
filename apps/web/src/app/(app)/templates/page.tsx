"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { FileCheck2, RefreshCw, Settings2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RequirePermission } from "@/features/auth/require-permission";
import { templateBuilderApi } from "@/features/template-builder/services/templateBuilderApi";
import type { TemplateCategory, TemplateFileFormat, TemplateStructureType, TemplateSummary } from "@/features/template-builder/types/templateBuilder";
import { ApiError } from "@/lib/api/http-client";

export default function TemplatesPage() {
  return (
    <RequirePermission permission="conferences:read">
      <TemplatesContent />
    </RequirePermission>
  );
}

function TemplatesContent() {
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [fileFormat, setFileFormat] = useState<TemplateFileFormat>("PDF");
  const [structureType, setStructureType] = useState<TemplateStructureType>("hierarchical");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const [templateResponse, categoryResponse] = await Promise.all([
        templateBuilderApi.listTemplates(),
        templateBuilderApi.listCategories(),
      ]);
      setTemplates(templateResponse.items ?? []);
      setCategories(categoryResponse.items ?? []);
      setCategoryId((current) => current || categoryResponse.items?.[0]?.id || "");
      setStatus("ready");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel carregar templates.");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  const createTemplate = async () => {
    if (!name.trim() || !categoryId) return;
    setBusy(true);
    try {
      const created = await templateBuilderApi.createTemplate({
        name: name.trim(),
        categoryId,
        fileFormat,
        structureType,
      });
      setName("");
      await load();
      window.location.assign(`/templates/${created.templateId}/builder`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel criar o template.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Template Builder"
        title="Templates"
        description="Crie e abra templates reais para mapear campos, annotations, sinais e regras tecnicas."
        action={(
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" /> Atualizar
          </Button>
        )}
      />

      {error && <ErrorState title="Operacao nao concluida" description={error} onRetry={() => setError(null)} />}

      <ThemeSurface className="p-5">
        <div className="grid gap-3 lg:grid-cols-[1fr_220px_140px_180px_auto]">
          <div className="space-y-1.5">
            <Label htmlFor="template-name">Nome</Label>
            <Input id="template-name" value={name} placeholder="Balancete Dominio PDF" onChange={(event) => setName(event.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="template-category">Categoria</Label>
            <select id="template-category" className="h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3 text-sm text-foreground" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="template-format">Formato</Label>
            <select id="template-format" className="h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3 text-sm text-foreground" value={fileFormat} onChange={(event) => setFileFormat(event.target.value as TemplateFileFormat)}>
              {["PDF", "XLSX", "XLS"].map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="template-structure">Estrutura</Label>
            <select id="template-structure" className="h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3 text-sm text-foreground" value={structureType} onChange={(event) => setStructureType(event.target.value as TemplateStructureType)}>
              {["text", "table", "hierarchical", "mixed", "unknown"].map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <Button className="self-end" onClick={() => void createTemplate()} disabled={busy || !name.trim() || !categoryId}>
            <FileCheck2 aria-hidden="true" /> Criar
          </Button>
        </div>
      </ThemeSurface>

      {status === "loading" && <LoadingState title="Carregando templates" description="Consultando Template Service pelo BFF." />}
      {status === "error" && <ErrorState onRetry={() => void load()} />}
      {status === "ready" && !templates.length && (
        <EmptyState icon={FileCheck2} title="Nenhum template ativo" description="Crie um template para iniciar o mapeamento visual." />
      )}
      {status === "ready" && Boolean(templates.length) && (
        <div className="grid gap-3 lg:grid-cols-2">
          {templates.map((template) => (
            <ThemeSurface key={template.templateId} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-white">{template.name}</h2>
                  <p className="mt-1 font-mono text-xs text-muted">{template.templateId}</p>
                </div>
                <Badge variant={template.status === "active" ? "success" : "neutral"}>{template.status}</Badge>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge variant="info">{template.fileFormat}</Badge>
                <Badge>{template.structureType}</Badge>
              </div>
              <div className="mt-5 flex justify-end border-t border-border pt-4">
                <Button asChild size="sm">
                  <Link href={`/templates/${template.templateId}/builder`}>
                    <Settings2 aria-hidden="true" /> Abrir builder
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

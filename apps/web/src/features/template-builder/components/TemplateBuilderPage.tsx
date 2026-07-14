"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { BookOpenCheck, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DocumentViewerShell } from "@/features/document-viewer/components/DocumentViewerShell";
import { useDocumentPreview } from "@/features/document-viewer/hooks/useDocumentPreview";
import { useDocumentSelection } from "@/features/document-viewer/hooks/useDocumentSelection";
import { ApiError } from "@/lib/api/http-client";
import { AnnotationList } from "./AnnotationList";
import { AnnotationPanel } from "./AnnotationPanel";
import { FieldEditor } from "./FieldEditor";
import { FieldTree } from "./FieldTree";
import { IdentificationSignalsPanel } from "./IdentificationSignalsPanel";
import { TemplateVersionPanel } from "./TemplateVersionPanel";
import { templateBuilderApi } from "../services/templateBuilderApi";
import type { FieldType, TemplateBuilderState, TemplateField } from "../types/templateBuilder";
import { annotationToEvidence } from "../types/templateBuilder";
import { defaultLabelFromPath } from "../utils/fieldPath";
import { selectedText, suggestStrategy } from "../utils/ruleSuggestion";

export function TemplateBuilderPage({ templateId, documentId }: { templateId: string; documentId?: string | null }) {
  const previewState = useDocumentPreview(documentId || "", Boolean(documentId));
  const { selection, setSelection, clearSelection } = useDocumentSelection();
  const [builderState, setBuilderState] = useState<TemplateBuilderState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState<TemplateField | null>(null);
  const [fieldPath, setFieldPath] = useState("");
  const [fieldType, setFieldType] = useState<FieldType>("text");
  const [generateRule, setGenerateRule] = useState(true);
  const [signalType, setSignalType] = useState("contains_text");
  const [signalValue, setSignalValue] = useState("");

  const loadBuilder = useCallback(async () => {
    setError(null);
    try {
      const state = await templateBuilderApi.getBuilderState(templateId);
      setBuilderState(state);
      setSelectedField((current) => current ? state.fields.find((field) => field.id === current.id) ?? null : state.fields[0] ?? null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel carregar o template.");
    }
  }, [templateId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadBuilder(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadBuilder]);

  const evidences = useMemo(() => {
    if (!builderState) return [];
    return builderState.annotations
      .map((annotation) => annotationToEvidence(annotation, builderState.fields.find((field) => field.id === annotation.fieldId)))
      .filter((item): item is NonNullable<typeof item> => Boolean(item));
  }, [builderState]);

  const createField = async () => {
    if (!fieldPath.trim()) return;
    setBusy("field");
    try {
      const field = await templateBuilderApi.createField(templateId, {
        fieldPath: fieldPath.trim(),
        label: defaultLabelFromPath(fieldPath.trim()),
        fieldType,
        isRequired: false,
        isRepeated: fieldPath.includes("[]") || fieldType === "array" || fieldType === "table",
        isArray: fieldPath.endsWith("[]") || fieldType === "array",
        isObject: fieldType === "object",
      });
      await loadBuilder();
      setSelectedField(field);
      setFieldPath("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel criar o campo.");
    } finally {
      setBusy(null);
    }
  };

  const saveAnnotation = async () => {
    if (!selection || !selectedField || !documentId) return;
    setBusy("annotation");
    try {
      const strategy = suggestStrategy(selection, selectedField);
      await templateBuilderApi.createAnnotationWithRule(templateId, {
        fieldId: selectedField.id,
        documentId,
        annotationType: selection.selection_type,
        selectedText: selectedText(selection),
        selectionPayload: selection,
        generateRule,
        ruleStrategy: strategy,
      });
      await loadBuilder();
      clearSelection();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel salvar a annotation.");
    } finally {
      setBusy(null);
    }
  };

  const deleteAnnotation = async (annotationId: string) => {
    setBusy("annotation");
    try {
      await templateBuilderApi.deleteAnnotation(templateId, annotationId);
      await loadBuilder();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel remover a annotation.");
    } finally {
      setBusy(null);
    }
  };

  const createSignal = async () => {
    if (!signalValue.trim()) return;
    setBusy("signal");
    try {
      await templateBuilderApi.createSignal(templateId, {
        signalType,
        value: signalValue.trim(),
        weight: 10,
        required: false,
        negative: false,
      });
      setSignalValue("");
      await loadBuilder();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel criar o sinal.");
    } finally {
      setBusy(null);
    }
  };

  const createDraft = async () => {
    setBusy("version");
    try {
      await templateBuilderApi.createVersion(templateId);
      await loadBuilder();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel criar a versao.");
    } finally {
      setBusy(null);
    }
  };

  const publishDraft = async (versionId: string) => {
    setBusy("version");
    try {
      await templateBuilderApi.publishVersion(templateId, versionId);
      await loadBuilder();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Nao foi possivel publicar a versao.");
    } finally {
      setBusy(null);
    }
  };

  if (!builderState && !error) {
    return <LoadingState title="Carregando template" description="Consultando o Template Service pelo BFF." />;
  }

  if (error && !builderState) {
    return <ErrorState title="Nao foi possivel abrir o builder" description={error} onRetry={() => void loadBuilder()} />;
  }

  const template = builderState!.template;

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Template Builder"
        title={template.name}
        description="Mapeie campos e objetos a partir de selecoes reais do preview estruturado."
        action={(
          <Button variant="secondary" onClick={() => void loadBuilder()}>
            <RefreshCw aria-hidden="true" /> Atualizar
          </Button>
        )}
      />

      {error && <ErrorState title="Acao nao concluida" description={error} onRetry={() => setError(null)} />}

      <ThemeSurface className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="info">{template.fileFormat}</Badge>
            <Badge>{template.structureType}</Badge>
            <Badge variant={template.status === "active" ? "success" : "neutral"}>{template.status}</Badge>
            {documentId && <span className="font-mono text-xs text-muted">{documentId}</span>}
          </div>
          <TemplateVersionPanel
            activeVersion={builderState!.activeVersion}
            draftVersion={builderState!.draftVersion}
            onCreateDraft={() => void createDraft()}
            onPublish={(versionId) => void publishDraft(versionId)}
            busy={busy === "version"}
          />
        </div>
      </ThemeSurface>

      <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <ThemeSurface className="space-y-5 p-5">
          <div>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-white">Campos</h2>
              <BookOpenCheck className="size-4 text-primary" aria-hidden="true" />
            </div>
            <p className="mt-1 text-sm text-muted">Objetos, arrays e campos mapeados do template.</p>
          </div>
          <FieldTree fields={builderState!.fields} selectedFieldId={selectedField?.id} onSelect={setSelectedField} />
          <FieldEditor
            fieldPath={fieldPath}
            fieldType={fieldType}
            onFieldPathChange={setFieldPath}
            onFieldTypeChange={setFieldType}
            onSubmit={() => void createField()}
            busy={busy === "field"}
          />
          <div className="space-y-3 border-t border-border pt-4">
            <h3 className="text-sm font-semibold text-white">Sinais de identificacao</h3>
            <IdentificationSignalsPanel
              signals={builderState!.identificationSignals}
              signalType={signalType}
              signalValue={signalValue}
              onSignalTypeChange={setSignalType}
              onSignalValueChange={setSignalValue}
              onCreate={() => void createSignal()}
              busy={busy === "signal"}
            />
          </div>
          <div className="space-y-3 border-t border-border pt-4">
            <h3 className="text-sm font-semibold text-white">Annotations</h3>
            <AnnotationList
              annotations={builderState!.annotations}
              fields={builderState!.fields}
              onDelete={(annotationId) => void deleteAnnotation(annotationId)}
            />
          </div>
        </ThemeSurface>

        <DocumentViewerShell
          document={previewState.document}
          preview={previewState.preview}
          state={documentId ? previewState.state : "preview_missing"}
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
          sidePanel={(
            <AnnotationPanel
              selection={selection}
              selectedField={selectedField}
              generateRule={generateRule}
              onGenerateRuleChange={setGenerateRule}
              onSave={() => void saveAnnotation()}
              onClear={clearSelection}
              busy={busy === "annotation"}
            />
          )}
        />
      </div>
    </div>
  );
}

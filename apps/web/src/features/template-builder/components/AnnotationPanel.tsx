"use client";

import { CheckCircle2, Clipboard, Eraser } from "lucide-react";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DocumentSelection } from "@/features/document-viewer/types/selection";
import type { TemplateField } from "../types/templateBuilder";
import { selectedText, selectionLabel, suggestStrategy } from "../utils/ruleSuggestion";

export function AnnotationPanel({
  selection,
  selectedField,
  generateRule,
  onGenerateRuleChange,
  onSave,
  onClear,
  busy,
}: {
  selection: DocumentSelection | null;
  selectedField: TemplateField | null;
  generateRule: boolean;
  onGenerateRuleChange: (value: boolean) => void;
  onSave: () => void;
  onClear: () => void;
  busy?: boolean;
}) {
  const strategy = suggestStrategy(selection, selectedField);
  const text = selectedText(selection);
  return (
    <ThemeSurface className="sticky top-24 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Badge variant={selection ? "info" : "neutral"}>{selectionLabel(selection)}</Badge>
          <h2 className="mt-3 text-lg font-semibold text-white">Associacao visual</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Escolha um campo e salve a selecao como annotation reutilizavel do template.
          </p>
        </div>
        <span className="grid size-10 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-muted-strong">
          <Clipboard className="size-4" aria-hidden="true" />
        </span>
      </div>

      <div className="mt-5 space-y-4">
        <div className="rounded-lg border border-border bg-black/15 p-3 text-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Campo selecionado</p>
          <p className="mt-1 text-white">{selectedField?.fieldPath ?? "Nenhum campo escolhido"}</p>
        </div>
        {text && (
          <p className="rounded-lg border border-primary/15 bg-primary/8 p-3 text-sm text-primary">{text}</p>
        )}
        {selection && (
          <pre className="max-h-56 overflow-auto rounded-lg border border-border bg-black/25 p-3 text-xs leading-5 text-muted-strong">
            {JSON.stringify(selection, null, 2)}
          </pre>
        )}
        <label className="flex items-center gap-2 text-sm text-muted-strong">
          <input
            type="checkbox"
            checked={generateRule}
            onChange={(event) => onGenerateRuleChange(event.target.checked)}
          />
          Gerar regra tecnica sugerida
        </label>
        <div className="rounded-lg border border-border bg-black/15 p-3 text-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Regra sugerida</p>
          <p className="mt-1 font-mono text-primary">{strategy ?? "Selecione um item"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={onSave} disabled={!selection || !selectedField || busy}>
            <CheckCircle2 aria-hidden="true" /> {busy ? "Salvando" : "Salvar annotation"}
          </Button>
          <Button type="button" variant="ghost" onClick={onClear}>
            <Eraser aria-hidden="true" /> Limpar
          </Button>
        </div>
      </div>
    </ThemeSurface>
  );
}

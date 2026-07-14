"use client";

import { useMemo, useState } from "react";
import { Clipboard, Eraser, MousePointer2 } from "lucide-react";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DocumentSelection } from "../types/selection";

function selectionTitle(selection: DocumentSelection | null) {
  if (!selection) return "Nenhuma seleção";
  return selection.selection_type.replaceAll("_", " ");
}

export function SelectionPanel({
  selection,
  onClear,
}: {
  selection: DocumentSelection | null;
  onClear: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const json = useMemo(() => (selection ? JSON.stringify(selection, null, 2) : ""), [selection]);

  async function copyJson() {
    if (!json) return;
    await navigator.clipboard?.writeText(json);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }

  return (
    <ThemeSurface className="sticky top-24 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Badge variant={selection ? "info" : "neutral"}>{selectionTitle(selection)}</Badge>
          <h2 className="mt-3 text-lg font-semibold text-white">Seleção atual</h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            Use esta seleção como payload técnico para anotações e templates nas próximas fases.
          </p>
        </div>
        <span className="grid size-10 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-muted-strong">
          <MousePointer2 className="size-4" aria-hidden="true" />
        </span>
      </div>

      {!selection ? (
        <div className="mt-6 rounded-lg border border-dashed border-border p-4 text-sm text-muted">
          Clique em um bloco PDF, célula Excel, coluna, área ou tabela candidata para ver o objeto de seleção aqui.
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          {"text" in selection && <p className="rounded-lg border border-primary/15 bg-primary/8 p-3 text-sm text-primary">{selection.text}</p>}
          {"cell" in selection && (
            <p className="rounded-lg border border-primary/15 bg-primary/8 p-3 text-sm text-primary">
              {selection.cell.address}: {String(selection.cell.value ?? "")}
            </p>
          )}
          <pre className="max-h-[420px] overflow-auto rounded-lg border border-border bg-black/25 p-3 text-xs leading-5 text-muted-strong">
            {json}
          </pre>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={() => void copyJson()}>
              <Clipboard aria-hidden="true" /> {copied ? "Copiado" : "Copiar JSON"}
            </Button>
            <Button variant="ghost" size="sm" onClick={onClear}>
              <Eraser aria-hidden="true" /> Limpar
            </Button>
          </div>
        </div>
      )}
    </ThemeSurface>
  );
}

"use client";

import { useMemo, useState } from "react";
import { EmptyState } from "@/components/states/empty-state";
import type { ExcelDocumentPreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";
import { ExcelGrid } from "./ExcelGrid";
import { ExcelSheetTabs } from "./ExcelSheetTabs";

export function ExcelDocumentViewer({
  preview,
  selection,
  evidences,
  onSelect,
}: {
  preview: ExcelDocumentPreview;
  selection: DocumentSelection | null;
  evidences: EvidenceHighlight[];
  onSelect: (selection: DocumentSelection) => void;
}) {
  const [activeIndex, setActiveIndex] = useState(preview.sheets[0]?.index ?? 0);
  const activeSheet = useMemo(
    () => preview.sheets.find((sheet) => sheet.index === activeIndex) || preview.sheets[0],
    [activeIndex, preview.sheets],
  );

  if (!activeSheet) {
    return (
      <EmptyState
        title="Preview Excel vazio"
        description="O backend retornou um preview pronto, mas sem abas renderizáveis."
      />
    );
  }

  return (
    <div className="space-y-4 rounded-xl border border-border bg-white/[0.025] p-4">
      <ExcelSheetTabs sheets={preview.sheets} activeIndex={activeSheet.index} onChange={setActiveIndex} />
      <div className="flex flex-wrap gap-2 text-xs text-muted">
        <span>{activeSheet.max_row} linhas</span>
        <span>·</span>
        <span>{activeSheet.max_column} colunas</span>
        <span>·</span>
        <span>{activeSheet.merged_cells.length} mesclagens</span>
        <span>·</span>
        <span>{activeSheet.detected_tables.length} tabelas candidatas</span>
      </div>
      <ExcelGrid
        documentId={preview.document_id}
        sheet={activeSheet}
        selection={selection}
        evidences={evidences}
        onSelect={onSelect}
      />
    </div>
  );
}

"use client";

import { cn } from "@/lib/utils";
import type { PdfPagePreview } from "../types/preview";
import type { DocumentSelection } from "../types/selection";
import { buildPdfTableSelection, buildPdfTextSelection } from "../utils/selectionBuilders";
import { isSameBox, scalePdfBox } from "../utils/pdfCoordinates";

function textStyle(style: ReturnType<typeof scalePdfBox>) {
  const fontSize = Math.max(7, Math.min(13, style.height * 0.82));
  return {
    ...style,
    fontSize,
    lineHeight: `${Math.max(8, style.height)}px`,
  };
}

export function PdfTextOverlay({
  documentId,
  page,
  scale,
  selection,
  onSelect,
}: {
  documentId: string;
  page: PdfPagePreview;
  scale: number;
  selection: DocumentSelection | null;
  onSelect: (selection: DocumentSelection) => void;
}) {
  return (
    <>
      {page.text_blocks.map((block) => {
        const style = scalePdfBox(block.bbox, scale);
        const selected = selection?.selection_type === "pdf_text_block" && isSameBox(selection.bbox, block.bbox);
        return (
          <button
            key={block.block_id}
            type="button"
            className={cn(
              "absolute rounded-sm border text-left transition hover:border-primary hover:bg-primary/8 focus:outline-none focus:ring-2 focus:ring-primary/60",
              selected ? "border-primary bg-primary/14" : "border-transparent bg-transparent",
            )}
            style={style}
            title={block.text}
            aria-label={`Selecionar bloco: ${block.text}`}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(buildPdfTextSelection(documentId, page.page_number, block, "pdf_text_block"));
            }}
          />
        );
      })}

      {page.lines.map((line) => {
        const style = scalePdfBox(line.bbox, scale);
        const selected = selection?.selection_type === "pdf_line" && isSameBox(selection.bbox, line.bbox);
        return (
          <button
            key={line.line_id}
            type="button"
            className={cn(
              "absolute overflow-visible whitespace-pre rounded-sm border border-transparent px-0.5 text-left font-mono text-slate-950 transition hover:border-violet/70 hover:bg-violet/10 focus:outline-none focus:ring-2 focus:ring-violet/60",
              selected && "border-violet bg-violet/16 shadow-[0_0_18px_rgba(167,139,250,.28)]",
            )}
            style={textStyle(style)}
            title={line.text}
            aria-label={`Selecionar linha: ${line.text}`}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(buildPdfTextSelection(documentId, page.page_number, line, "pdf_line"));
            }}
          >
            {line.text}
          </button>
        );
      })}

      {page.tables.map((table) => {
        const style = scalePdfBox(table.bbox, scale);
        const selected = selection?.selection_type === "pdf_table_candidate" && selection.table_id === table.table_id;
        return (
          <button
            key={table.table_id}
            type="button"
            className={cn(
              "absolute rounded-md border-2 border-dashed transition hover:border-warning hover:bg-warning/8 focus:outline-none focus:ring-2 focus:ring-warning/60",
              selected ? "border-warning bg-warning/12" : "border-warning/35 bg-transparent",
            )}
            style={style}
            aria-label={`Selecionar tabela candidata ${table.table_id}`}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(buildPdfTableSelection(documentId, page.page_number, table));
            }}
          />
        );
      })}
    </>
  );
}

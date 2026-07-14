"use client";

import { cn } from "@/lib/utils";
import type { PdfPagePreview } from "../types/preview";
import type { DocumentSelection } from "../types/selection";
import { buildPdfTableSelection, buildPdfTextSelection } from "../utils/selectionBuilders";
import { isSameBox, scalePdfBox } from "../utils/pdfCoordinates";

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
              "absolute rounded-sm border text-left transition hover:border-primary hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-primary/60",
              selected ? "border-primary bg-primary/18" : "border-primary/25 bg-primary/[0.025]",
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
              "absolute rounded-sm border border-transparent transition hover:border-violet/70 hover:bg-violet/12 focus:outline-none focus:ring-2 focus:ring-violet/60",
              selected && "border-violet bg-violet/18",
            )}
            style={style}
            title={line.text}
            aria-label={`Selecionar linha: ${line.text}`}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(buildPdfTextSelection(documentId, page.page_number, line, "pdf_line"));
            }}
          />
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
              "absolute rounded-md border-2 border-dashed transition hover:border-warning hover:bg-warning/10 focus:outline-none focus:ring-2 focus:ring-warning/60",
              selected ? "border-warning bg-warning/18" : "border-warning/45 bg-warning/[0.03]",
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

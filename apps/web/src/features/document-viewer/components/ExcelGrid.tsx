"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ExcelCellPreview, ExcelSheetPreview } from "../types/preview";
import type { DocumentSelection, EvidenceHighlight } from "../types/selection";
import { isExcelEvidenceCell } from "./EvidenceHighlightLayer";
import { buildCellMap, cellKey, columnLetter, isCellInRange, parseRange } from "../utils/excelCoordinates";
import {
  buildExcelCellSelection,
  buildExcelColumnSelection,
  buildExcelRangeSelection,
  buildExcelRowSelection,
  buildExcelTableSelection,
} from "../utils/selectionBuilders";

const MAX_VISIBLE_ROWS = 160;
const MAX_VISIBLE_COLUMNS = 40;

function cellDisplayValue(cell?: ExcelCellPreview) {
  if (!cell || cell.value === null || cell.value === undefined) return "";
  if (typeof cell.value === "object") return JSON.stringify(cell.value);
  return String(cell.value);
}

function selectedRange(selection: DocumentSelection | null) {
  if (selection?.selection_type !== "excel_range") return null;
  return {
    start_row: selection.range.start_row,
    end_row: selection.range.end_row,
    start_column: selection.range.start_column,
    end_column: selection.range.end_column,
  };
}

export function ExcelGrid({
  documentId,
  sheet,
  selection,
  evidences,
  onSelect,
}: {
  documentId: string;
  sheet: ExcelSheetPreview;
  selection: DocumentSelection | null;
  evidences: EvidenceHighlight[];
  onSelect: (selection: DocumentSelection) => void;
}) {
  const cellMap = useMemo(() => buildCellMap(sheet), [sheet]);
  const [dragStart, setDragStart] = useState<{ row: number; column: number } | null>(null);
  const [dragEnd, setDragEnd] = useState<{ row: number; column: number } | null>(null);
  const visibleRows = Math.min(sheet.max_row || 1, MAX_VISIBLE_ROWS);
  const visibleColumns = Math.min(sheet.max_column || 1, MAX_VISIBLE_COLUMNS);
  const activeRange = dragStart && dragEnd
    ? {
        start_row: Math.min(dragStart.row, dragEnd.row),
        end_row: Math.max(dragStart.row, dragEnd.row),
        start_column: Math.min(dragStart.column, dragEnd.column),
        end_column: Math.max(dragStart.column, dragEnd.column),
      }
    : selectedRange(selection);

  function headerForColumn(column: number) {
    const headerRow = sheet.detected_headers[0]?.row;
    if (!headerRow) return null;
    return cellDisplayValue(cellMap.get(cellKey(headerRow, column))) || null;
  }

  function selectCell(cell: ExcelCellPreview) {
    onSelect(buildExcelCellSelection(documentId, sheet, cell));
  }

  return (
    <div className="space-y-4">
      {sheet.detected_tables.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sheet.detected_tables.map((table) => (
            <button
              key={table.table_id}
              type="button"
              className="rounded-lg border border-warning/30 bg-warning/8 px-3 py-2 text-xs font-semibold text-warning transition hover:bg-warning/14"
              onClick={() => onSelect(buildExcelTableSelection(documentId, sheet, table))}
            >
              Tabela candidata {table.range} · {Math.round(table.confidence * 100)}%
            </button>
          ))}
        </div>
      )}

      {(sheet.max_row > MAX_VISIBLE_ROWS || sheet.max_column > MAX_VISIBLE_COLUMNS) && (
        <div className="rounded-lg border border-border bg-white/[0.035] p-3 text-xs text-muted">
          Exibindo {visibleRows} linhas e {visibleColumns} colunas para manter a tela responsiva. A virtualização completa fica preparada para evolução futura.
        </div>
      )}

      <div className="overflow-auto rounded-xl border border-border bg-black/20">
        <table className="min-w-max border-separate border-spacing-0 text-sm">
          <thead className="sticky top-0 z-10 bg-background">
            <tr>
              <th className="sticky left-0 z-20 w-12 border-b border-r border-border bg-background p-2 text-xs text-muted">#</th>
              {Array.from({ length: visibleColumns }, (_, index) => index + 1).map((column) => (
                <th
                  key={column}
                  className="min-w-32 border-b border-r border-border bg-background p-0"
                >
                  <button
                    type="button"
                    className={cn(
                      "flex w-full flex-col items-center gap-1 px-3 py-2 text-xs text-muted-strong transition hover:bg-primary/10 hover:text-primary",
                      selection?.selection_type === "excel_column" && selection.column === column && "bg-primary/18 text-primary",
                    )}
                    onClick={() => onSelect(buildExcelColumnSelection(documentId, sheet, column, headerForColumn(column)))}
                  >
                    <span>{columnLetter(column)}</span>
                    {headerForColumn(column) && <span className="max-w-28 truncate text-[0.65rem] text-muted">{headerForColumn(column)}</span>}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: visibleRows }, (_, rowIndex) => rowIndex + 1).map((row) => (
              <tr key={row}>
                <th className="sticky left-0 z-10 border-b border-r border-border bg-background p-0">
                  <button
                    type="button"
                    className={cn(
                      "grid h-9 w-12 place-items-center text-xs text-muted transition hover:bg-violet/10 hover:text-violet",
                      selection?.selection_type === "excel_row" && selection.row === row && "bg-violet/18 text-violet",
                    )}
                    onClick={() => onSelect(buildExcelRowSelection(documentId, sheet, row))}
                  >
                    {row}
                  </button>
                </th>
                {Array.from({ length: visibleColumns }, (_, columnIndex) => columnIndex + 1).map((column) => {
                  const cell = cellMap.get(cellKey(row, column));
                  const value = cellDisplayValue(cell);
                  const isHeader = sheet.detected_headers.some((header) => header.row === row);
                  const isEvidence = isExcelEvidenceCell(sheet.name, row, column, evidences);
                  const isRange = isCellInRange(row, column, activeRange);
                  const tableRange = sheet.detected_tables.find((table) => isCellInRange(row, column, parseRange(table.range)));
                  const isSelectedCell = selection?.selection_type === "excel_cell" && selection.cell.address === cell?.address;
                  return (
                    <td
                      key={`${row}-${column}`}
                      className={cn(
                        "h-9 min-w-32 max-w-52 border-b border-r border-border p-0",
                        isHeader && "bg-primary/8",
                        tableRange && "bg-warning/[0.035]",
                        isEvidence && "bg-warning/18",
                        isRange && "bg-primary/16",
                        isSelectedCell && "bg-primary/24",
                      )}
                    >
                      <button
                        type="button"
                        className="h-full w-full truncate px-3 text-left text-xs text-foreground hover:bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-primary/50"
                        title={value}
                        onMouseDown={() => {
                          setDragStart({ row, column });
                          setDragEnd({ row, column });
                        }}
                        onMouseEnter={() => {
                          if (dragStart) setDragEnd({ row, column });
                        }}
                        onMouseUp={() => {
                          if (dragStart && (dragStart.row !== row || dragStart.column !== column)) {
                            onSelect(buildExcelRangeSelection(documentId, sheet, dragStart, { row, column }));
                          } else if (cell) {
                            selectCell(cell);
                          }
                          setDragStart(null);
                          setDragEnd(null);
                        }}
                        aria-label={cell ? `Selecionar célula ${cell.address}` : `Selecionar célula ${columnLetter(column)}${row}`}
                      >
                        {cell?.is_merged && <Badge variant="violet" className="mr-1 align-middle">mesclada</Badge>}
                        {value}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

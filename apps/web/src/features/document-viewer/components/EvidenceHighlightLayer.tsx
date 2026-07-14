"use client";

import type { EvidenceHighlight } from "../types/selection";
import { parseRange, isCellInRange } from "../utils/excelCoordinates";
import { scalePdfBox } from "../utils/pdfCoordinates";

export function PdfEvidenceHighlightLayer({
  pageNumber,
  scale,
  evidences,
}: {
  pageNumber: number;
  scale: number;
  evidences: EvidenceHighlight[];
}) {
  return (
    <>
      {evidences.map((item, index) => {
          if (item.evidence_type !== "pdf" || item.page_number !== pageNumber) return null;
          const style = scalePdfBox(item.bbox, scale);
          return (
            <div
              key={`${item.label}-${index}`}
              className="pointer-events-none absolute rounded-md border border-warning/80 bg-warning/18 shadow-[0_0_24px_rgba(245,158,11,.16)]"
              style={style}
              title={item.label}
              data-testid="pdf-evidence-highlight"
            />
          );
        })}
    </>
  );
}

export function isExcelEvidenceCell(sheetName: string, row: number, column: number, evidences: EvidenceHighlight[]) {
  return evidences.some((item) => {
    if (item.evidence_type !== "excel" || item.sheet_name !== sheetName) return false;
    return isCellInRange(row, column, parseRange(item.cell_range));
  });
}

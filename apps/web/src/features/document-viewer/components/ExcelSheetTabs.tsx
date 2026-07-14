"use client";

import { cn } from "@/lib/utils";
import type { ExcelSheetPreview } from "../types/preview";

export function ExcelSheetTabs({
  sheets,
  activeIndex,
  onChange,
}: {
  sheets: ExcelSheetPreview[];
  activeIndex: number;
  onChange: (index: number) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto rounded-xl border border-border bg-white/[0.035] p-2">
      {sheets.map((sheet) => (
        <button
          key={sheet.sheet_id}
          type="button"
          onClick={() => onChange(sheet.index)}
          className={cn(
            "rounded-lg px-3 py-2 text-sm font-semibold transition",
            activeIndex === sheet.index
              ? "bg-primary text-primary-foreground"
              : "text-muted-strong hover:bg-white/[0.06] hover:text-white",
          )}
        >
          {sheet.name}
        </button>
      ))}
    </div>
  );
}

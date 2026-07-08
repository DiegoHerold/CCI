import { ScanLine } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProductLogo({ compact = false, className }: { compact?: boolean; className?: string }) {
  return (
    <div className={cn("flex items-center gap-3", className)} aria-label="CCI — Conferência Contábil Inteligente">
      <span className="relative grid size-10 shrink-0 place-items-center overflow-hidden rounded-xl border border-primary/25 bg-primary/8 text-primary shadow-[inset_0_1px_rgba(255,255,255,.08),0_0_28px_rgba(100,216,255,.08)]">
        <ScanLine className="size-5" strokeWidth={1.8} aria-hidden="true" />
        <span className="absolute inset-x-2 bottom-1.5 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
      </span>
      {!compact && (
        <span className="min-w-0">
          <span className="block text-sm font-bold tracking-[0.17em] text-white">CCI</span>
          <span className="block truncate text-[0.67rem] font-medium tracking-[0.015em] text-muted">
            Conferência Contábil Inteligente
          </span>
        </span>
      )}
    </div>
  );
}

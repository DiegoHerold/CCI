import type { LucideIcon } from "lucide-react";
import { Clock3 } from "lucide-react";

export function ModuleCard({ icon: Icon, title, description, phase }: { icon: LucideIcon; title: string; description: string; phase: string }) {
  return (
    <div className="rounded-xl border border-border bg-white/[0.018] p-4 transition hover:border-border-strong hover:bg-white/[0.028]">
      <div className="flex items-center justify-between">
        <span className="grid size-9 place-items-center rounded-lg border border-white/8 bg-white/[0.035] text-muted-strong"><Icon className="size-4" aria-hidden="true" /></span>
        <span className="flex items-center gap-1.5 text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-muted/65"><Clock3 className="size-3" /> {phase}</span>
      </div>
      <h3 className="mt-4 text-sm font-semibold text-white">{title}</h3>
      <p className="mt-1.5 text-xs leading-5 text-muted">{description}</p>
    </div>
  );
}

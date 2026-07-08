import type { LucideIcon } from "lucide-react";
import { ArrowUpRight } from "lucide-react";
import { ThemeSurface } from "@/components/layout/theme-surface";

export function MetricCard({ label, value, description, icon: Icon, accent = "primary" }: { label: string; value: string | number; description: string; icon: LucideIcon; accent?: "primary" | "violet" | "success" | "warning" }) {
  const colors = { primary: "text-primary bg-primary/8 border-primary/15", violet: "text-violet bg-violet/8 border-violet/15", success: "text-success bg-success/8 border-success/15", warning: "text-warning bg-warning/8 border-warning/15" };
  return (
    <ThemeSurface className="group relative overflow-hidden p-5 transition duration-300 hover:-translate-y-0.5 hover:border-border-strong">
      <ArrowUpRight className="absolute right-4 top-4 size-3.5 text-muted/35 transition group-hover:text-muted" aria-hidden="true" />
      <span className={`grid size-9 place-items-center rounded-lg border ${colors[accent]}`}><Icon className="size-4" aria-hidden="true" /></span>
      <p className="mt-5 text-xs font-medium text-muted">{label}</p>
      <p className="mt-1.5 text-2xl font-semibold tracking-[-0.04em] text-white">{value}</p>
      <p className="mt-2 text-xs leading-5 text-muted/75">{description}</p>
    </ThemeSurface>
  );
}

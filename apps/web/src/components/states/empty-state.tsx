import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  className,
}: {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <ThemeSurface className={cn("relative overflow-hidden p-7", className)}>
      <div className="absolute -right-12 -top-12 size-36 rounded-full bg-primary/[0.035] blur-2xl" />
      <div className="relative flex flex-col items-start gap-4 sm:flex-row sm:items-center">
        <span className="grid size-12 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.035] text-muted-strong">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <div className="flex-1">
          <h2 className="font-semibold text-white">{title}</h2>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted">{description}</p>
        </div>
        {action}
      </div>
    </ThemeSurface>
  );
}

"use client";

import { CalendarDays } from "lucide-react";
import { useOperationalContext } from "./operational-context-provider";

export function formatCompetence(period?: string | null) {
  if (!period || !/^\d{4}-\d{2}$/.test(period)) return "Não selecionada";
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

export function CompetenceSelector() {
  const { data, selectedClient } = useOperationalContext();
  const period = selectedClient ? data?.currentCompetence.period : null;
  return (
    <div className="hidden h-10 items-center gap-2 rounded-lg border border-border bg-black/15 px-3 text-xs md:flex">
      <CalendarDays className="size-4 text-violet" aria-hidden="true" />
      <span className="text-muted">Competência</span>
      <span className="font-semibold text-foreground">{formatCompetence(period)}</span>
    </div>
  );
}

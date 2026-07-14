"use client";

import { useState } from "react";
import { CalendarDays } from "lucide-react";
import { useOperationalContext } from "./operational-context-provider";

export function formatCompetence(period?: string | null) {
  if (!period || !/^\d{4}-\d{2}$/.test(period)) return "Nao selecionada";
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

export function CompetenceSelector() {
  const { selectedClient, selectedCompetencePeriod, selectCompetence } = useOperationalContext();
  const [saving, setSaving] = useState(false);
  const period = selectedClient ? selectedCompetencePeriod : null;

  return (
    <label className="hidden h-10 items-center gap-2 rounded-lg border border-border bg-black/15 px-3 text-xs transition hover:border-border-strong md:flex">
      <CalendarDays className="size-4 text-violet" aria-hidden="true" />
      <span className="text-muted">Competencia</span>
      <input
        aria-label="Competencia atual"
        type="month"
        value={period ?? ""}
        disabled={!selectedClient || saving}
        onChange={async (event) => {
          if (!event.target.value) return;
          setSaving(true);
          try {
            await selectCompetence(event.target.value);
          } finally {
            setSaving(false);
          }
        }}
        className="h-8 w-[7.25rem] rounded-md border border-transparent bg-transparent px-1 text-xs font-semibold text-foreground outline-none transition hover:border-white/10 focus:border-violet/50 disabled:opacity-60"
      />
    </label>
  );
}

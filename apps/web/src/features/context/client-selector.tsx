"use client";

import { Building2, ChevronDown } from "lucide-react";
import { useState } from "react";
import { useOperationalContext } from "./operational-context-provider";

export function ClientSelector() {
  const { data, selectedClientId, selectClient, status } = useOperationalContext();
  const [saving, setSaving] = useState(false);

  if (status === "loading") return <div className="h-10 w-48 animate-pulse rounded-lg bg-white/[0.04]" />;
  if (!data?.clients.length) {
    return <span className="hidden text-xs text-muted sm:inline">Nenhum cliente vinculado</span>;
  }

  return (
    <label className="relative flex min-w-0 items-center gap-2 rounded-lg border border-border bg-black/15 px-3 transition hover:border-border-strong">
      <Building2 className="size-4 shrink-0 text-primary" aria-hidden="true" />
      <span className="sr-only">Cliente atual</span>
      <select
        aria-label="Cliente atual"
        value={selectedClientId ?? ""}
        disabled={saving}
        onChange={async (event) => {
          if (!event.target.value) return;
          setSaving(true);
          try { await selectClient(event.target.value); } finally { setSaving(false); }
        }}
        className="h-9 min-w-0 max-w-48 appearance-none bg-transparent pr-6 text-xs font-medium text-foreground outline-none"
      >
        <option value="" disabled>Selecionar cliente</option>
        {data.clients.map((client) => (
          <option key={client.id} value={client.id}>{client.tradeName || client.name}</option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 size-3.5 text-muted" aria-hidden="true" />
    </label>
  );
}

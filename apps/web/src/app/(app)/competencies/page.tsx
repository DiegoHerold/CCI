"use client";

import { useCallback, useEffect, useState } from "react";
import { CalendarRange } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { Badge } from "@/components/ui/badge";
import { RequirePermission } from "@/features/auth/require-permission";
import { formatCompetence } from "@/features/context/competence-selector";
import { useOperationalContext } from "@/features/context/operational-context-provider";
import { clientContextApi } from "@/lib/api/client-context-api";
import type { Competency } from "@/types/api";

export default function CompetenciesPage() {
  return <RequirePermission permission="client-competencies:read"><CompetenciesContent /></RequirePermission>;
}

function CompetenciesContent() {
  const { selectedClient } = useOperationalContext();
  const [items, setItems] = useState<Competency[]>([]);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const load = useCallback(async () => {
    if (!selectedClient) return;
    setState("loading");
    setItems([]);
    try { const response = await clientContextApi.listCompetencies(selectedClient.id); setItems(response.items); setState("ready"); }
    catch { setState("error"); }
  }, [selectedClient]);
  useEffect(() => {
    if (!selectedClient) return;
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load, selectedClient]);

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Control Plane" title="Competências" description="Períodos mensais reais do cliente selecionado, consultados pelo BFF no Client Service." />
      {!selectedClient && <EmptyState icon={CalendarRange} title="Nenhum cliente selecionado" description="Selecione um cliente no topo para consultar suas competências autorizadas." />}
      {selectedClient && state === "loading" && <LoadingState title="Carregando competências" description={`Consultando ${selectedClient.tradeName || selectedClient.name}.`} />}
      {selectedClient && state === "error" && <ErrorState onRetry={() => void load()} />}
      {selectedClient && state === "ready" && !items.length && <EmptyState icon={CalendarRange} title="Nenhuma competência cadastrada" description="O Client Service ainda não possui competências para este cliente. Esta Web não cria períodos automaticamente." />}
      {selectedClient && state === "ready" && Boolean(items.length) && <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{items.map((item) => <ThemeSurface key={item.id} className="flex items-center gap-4 p-5"><span className="grid size-10 place-items-center rounded-xl border border-violet/15 bg-violet/7 text-violet"><CalendarRange className="size-4.5" /></span><div className="flex-1"><p className="font-semibold text-white">{formatCompetence(item.period)}</p><p className="mt-1 text-xs text-muted">{item.folderPath || "Pasta não resolvida"}</p></div><Badge variant="info">{item.status}</Badge></ThemeSurface>)}</div>}
    </div>
  );
}

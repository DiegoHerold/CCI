"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { clientContextApi } from "@/lib/api/client-context-api";
import type { ClientContextResponse, ClientSummary } from "@/types/api";

interface OperationalContextValue {
  data: ClientContextResponse | null;
  selectedClient: ClientSummary | null;
  selectedClientId: string | null;
  selectedCompetencePeriod: string | null;
  status: "loading" | "ready" | "error";
  error: string | null;
  selectClient: (clientId: string) => Promise<void>;
  selectCompetence: (period: string) => Promise<void>;
  reload: () => Promise<void>;
}

const OperationalContext = createContext<OperationalContextValue | null>(null);

export function OperationalContextProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<ClientContextResponse | null>(null);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [selectedCompetencePeriod, setSelectedCompetencePeriod] = useState<string | null>(null);
  const [status, setStatus] = useState<OperationalContextValue["status"]>("loading");
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const context = await clientContextApi.get();
      setData(context);
      setSelectedClientId(
        context.defaultClientId && context.clients.some((client) => client.id === context.defaultClientId)
          ? context.defaultClientId
          : null,
      );
      setSelectedCompetencePeriod(context.currentCompetence.period);
      setStatus("ready");
    } catch {
      setData(null);
      setSelectedClientId(null);
      setSelectedCompetencePeriod(null);
      setError("O contexto de clientes não está disponível.");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void reload(), 0);
    return () => window.clearTimeout(timeout);
  }, [reload]);

  useEffect(() => {
    const listener = () => void reload();
    window.addEventListener("cci:operational-context-refresh", listener);
    return () => window.removeEventListener("cci:operational-context-refresh", listener);
  }, [reload]);

  const selectClient = useCallback(async (clientId: string) => {
    if (!data?.clients.some((client) => client.id === clientId)) return;
    let competency = null;
    if (selectedCompetencePeriod) {
      try {
        competency = await clientContextApi.ensureCurrentCompetency(clientId, selectedCompetencePeriod);
      } catch {
        competency = null;
      }
    }
    await clientContextApi.updatePreference(clientId, competency?.period ?? null);
    setSelectedClientId(clientId);
    setData((current) => current ? {
      ...current,
      defaultClientId: clientId,
      currentCompetence: competency
        ? { period: competency.period, year: competency.year, month: competency.month }
        : current.currentCompetence,
    } : current);
  }, [data, selectedCompetencePeriod]);

  const selectCompetence = useCallback(async (period: string) => {
    if (!selectedClientId || !/^\d{4}-\d{2}$/.test(period)) return;
    const competency = await clientContextApi.ensureCurrentCompetency(selectedClientId, period);
    await clientContextApi.updatePreference(selectedClientId, competency.period);
    setSelectedCompetencePeriod(competency.period);
    setData((current) => current ? {
      ...current,
      defaultClientId: selectedClientId,
      currentCompetence: {
        period: competency.period,
        year: competency.year,
        month: competency.month,
      },
    } : current);
  }, [selectedClientId]);

  const selectedClient = useMemo(
    () => data?.clients.find((client) => client.id === selectedClientId) ?? null,
    [data, selectedClientId],
  );

  const value = useMemo(
    () => ({ data, selectedClient, selectedClientId, selectedCompetencePeriod, status, error, selectClient, selectCompetence, reload }),
    [data, selectedClient, selectedClientId, selectedCompetencePeriod, status, error, selectClient, selectCompetence, reload],
  );

  return <OperationalContext.Provider value={value}>{children}</OperationalContext.Provider>;
}

export function useOperationalContext() {
  const context = useContext(OperationalContext);
  if (!context) throw new Error("useOperationalContext must be used inside its provider");
  return context;
}

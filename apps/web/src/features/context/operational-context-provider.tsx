"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { clientContextApi } from "@/lib/api/client-context-api";
import type { ClientContextResponse, ClientSummary } from "@/types/api";

interface OperationalContextValue {
  data: ClientContextResponse | null;
  selectedClient: ClientSummary | null;
  selectedClientId: string | null;
  status: "loading" | "ready" | "error";
  error: string | null;
  selectClient: (clientId: string) => Promise<void>;
  reload: () => Promise<void>;
}

const OperationalContext = createContext<OperationalContextValue | null>(null);

export function OperationalContextProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<ClientContextResponse | null>(null);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
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
      setStatus("ready");
    } catch {
      setData(null);
      setSelectedClientId(null);
      setError("O contexto de clientes não está disponível.");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void reload(), 0);
    return () => window.clearTimeout(timeout);
  }, [reload]);

  const selectClient = useCallback(async (clientId: string) => {
    if (!data?.clients.some((client) => client.id === clientId)) return;
    await clientContextApi.updatePreference(clientId);
    setSelectedClientId(clientId);
    setData((current) => current ? { ...current, defaultClientId: clientId } : current);
  }, [data]);

  const selectedClient = useMemo(
    () => data?.clients.find((client) => client.id === selectedClientId) ?? null,
    [data, selectedClientId],
  );

  const value = useMemo(
    () => ({ data, selectedClient, selectedClientId, status, error, selectClient, reload }),
    [data, selectedClient, selectedClientId, status, error, selectClient, reload],
  );

  return <OperationalContext.Provider value={value}>{children}</OperationalContext.Provider>;
}

export function useOperationalContext() {
  const context = useContext(OperationalContext);
  if (!context) throw new Error("useOperationalContext must be used inside its provider");
  return context;
}

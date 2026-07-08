"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, RotateCcw } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { authApi } from "@/lib/api/auth-api";
import { clientContextApi } from "@/lib/api/client-context-api";
import { clientsApi } from "@/lib/api/clients-api";
import { usersApi } from "@/lib/api/users-api";
import { ApiError } from "@/lib/api/http-client";

type ServiceStatus = "checking" | "available" | "unavailable" | "not-implemented" | "forbidden" | "error";

interface ServiceCheck {
  key: string;
  label: string;
  route: string;
  description: string;
  run: () => Promise<unknown>;
}

const CHECKS: ServiceCheck[] = [
  { key: "auth-me", label: "Identidade", route: "GET /auth/me", description: "Sessão e permissões do usuário atual.", run: () => authApi.me() },
  { key: "users", label: "Usuários", route: "GET /users", description: "Listagem administrativa de usuários.", run: () => usersApi.list({ limit: 1 }) },
  { key: "clients", label: "Clientes", route: "GET /clients", description: "Cadastro de clientes do Client Service.", run: () => clientsApi.list({ limit: 1 }) },
  { key: "client-context", label: "Contexto operacional", route: "GET /client-context", description: "Clientes autorizados e competência de referência.", run: () => clientContextApi.get() },
];

function classify(error: unknown): ServiceStatus {
  if (!(error instanceof ApiError)) return "unavailable";
  if (error.status === 403) return "forbidden";
  if (error.status === 404) return "not-implemented";
  if (error.status === 501 || error.status === 503 || error.status === 0) return "unavailable";
  return "error";
}

const STATUS_LABEL: Record<ServiceStatus, { label: string; variant: "success" | "neutral" | "warning" | "danger" | "info" }> = {
  checking: { label: "Verificando…", variant: "neutral" },
  available: { label: "Disponível", variant: "success" },
  unavailable: { label: "Indisponível", variant: "warning" },
  "not-implemented": { label: "Não implementado", variant: "neutral" },
  forbidden: { label: "Sem permissão", variant: "info" },
  error: { label: "Erro", variant: "danger" },
};

export default function ServicesStatusPage() {
  const [statuses, setStatuses] = useState<Record<string, ServiceStatus>>(
    () => Object.fromEntries(CHECKS.map((check) => [check.key, "checking" as ServiceStatus])),
  );

  const runChecks = useCallback(() => {
    setStatuses(Object.fromEntries(CHECKS.map((check) => [check.key, "checking" as ServiceStatus])));
    for (const check of CHECKS) {
      check
        .run()
        .then(() => setStatuses((current) => ({ ...current, [check.key]: "available" })))
        .catch((error) => setStatuses((current) => ({ ...current, [check.key]: classify(error) })));
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => runChecks(), 0);
    return () => window.clearTimeout(timeout);
  }, [runChecks]);

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Diagnóstico"
        title="Status dos serviços"
        description="Verificação em tempo real dos endpoints que a Web depende no BFF. Nenhuma informação sensível é exibida aqui."
        action={<Button variant="secondary" onClick={runChecks}><RotateCcw aria-hidden="true" /> Verificar novamente</Button>}
      />

      <div className="grid gap-3 md:grid-cols-2">
        {CHECKS.map((check) => {
          const status = statuses[check.key] ?? "checking";
          const entry = STATUS_LABEL[status];
          return (
            <ThemeSurface key={check.key} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <span className="grid size-10 place-items-center rounded-xl border border-primary/15 bg-primary/7 text-primary"><Activity className="size-4.5" /></span>
                <Badge variant={entry.variant}><span className="size-1.5 rounded-full bg-current" /> {entry.label}</Badge>
              </div>
              <h2 className="mt-5 font-semibold text-white">{check.label}</h2>
              <p className="mt-1 font-mono text-xs text-muted">{check.route}</p>
              <p className="mt-3 text-xs leading-5 text-muted">{check.description}</p>
            </ThemeSurface>
          );
        })}
      </div>
    </div>
  );
}

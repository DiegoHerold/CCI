"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Building2, MapPin, Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { ClientStatusBadge } from "@/components/badges/client-status-badge";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { ServiceUnavailableState } from "@/components/states/service-unavailable-state";
import { SuccessNotice } from "@/components/states/success-notice";
import { Button } from "@/components/ui/button";
import { DataToolbar } from "@/components/ui/data-toolbar";
import { FormDrawer } from "@/components/ui/form-drawer";
import { RequirePermission } from "@/features/auth/require-permission";
import { useAuth } from "@/features/auth/auth-provider";
import { hasPermission } from "@/features/auth/permissions";
import { ClientForm } from "@/features/clients/client-form";
import { clientsApi } from "@/lib/api/clients-api";
import { ApiError } from "@/lib/api/http-client";
import { classifyApiError, friendlyErrorMessage } from "@/lib/api/error-utils";
import type { ClientRecord, CreateClientPayload } from "@/types/api";

type PageStatus = "loading" | "ready" | "error" | "unavailable";

export default function ClientsPage() {
  return <RequirePermission permission="clients:read"><ClientsContent /></RequirePermission>;
}

function ClientsContent() {
  const { user } = useAuth();
  const [items, setItems] = useState<ClientRecord[]>([]);
  const [status, setStatus] = useState<PageStatus>("loading");
  const [search, setSearch] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formUnavailable, setFormUnavailable] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (searchTerm: string) => {
    setStatus("loading");
    try {
      const response = await clientsApi.list({ search: searchTerm || undefined, limit: 50 });
      setItems(response.items ?? []);
      setStatus("ready");
    } catch (error) {
      if (classifyApiError(error) === "SERVICE_UNAVAILABLE") {
        setItems([]);
        setStatus("unavailable");
        return;
      }
      setItems([]);
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(""), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  function handleSearchChange(value: string) {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => void load(value), 350);
  }

  function openDrawer() {
    setFormError(null);
    setFormUnavailable(null);
    setDrawerOpen(true);
  }

  function closeDrawer() {
    setDrawerOpen(false);
    setFormError(null);
    setFormUnavailable(null);
  }

  async function handleCreate(payload: CreateClientPayload) {
    setSubmitting(true);
    setFormError(null);
    setFormUnavailable(null);
    try {
      await clientsApi.create(payload);
      setDrawerOpen(false);
      setSuccessMessage(`Cliente "${payload.name}" cadastrado com sucesso.`);
      await load(search);
    } catch (error) {
      const code = classifyApiError(error);
      if (code === "SERVICE_UNAVAILABLE") {
        setFormUnavailable(
          "Cadastro ainda não concluído. O formulário está pronto, mas o endpoint de criação de clientes ainda não está disponível no BFF. Nenhum cliente foi salvo.",
        );
        return;
      }
      const message = error instanceof ApiError
        ? friendlyErrorMessage(error, "Não foi possível cadastrar o cliente. Confira os dados e tente novamente.")
        : "Não foi possível cadastrar o cliente. Confira os dados e tente novamente.";
      setFormError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const canCreate = hasPermission(user, "clients:create");

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Control Plane"
        title="Clientes"
        description="Cadastro de clientes atendidos pela Biason, mantido pelo Client Service e exposto por este BFF."
        action={canCreate ? (
          <Button onClick={openDrawer}>
            <Plus aria-hidden="true" /> Novo cliente
          </Button>
        ) : undefined}
      />

      {successMessage && <SuccessNotice message={successMessage} />}

      <DataToolbar
        searchValue={search}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Pesquisar por razão social, nome fantasia ou CNPJ"
      />

      {status === "loading" && <LoadingState title="Carregando clientes" description="Consultando o Client Service pelo BFF." />}
      {status === "error" && <ErrorState onRetry={() => void load(search)} />}
      {status === "unavailable" && (
        <ServiceUnavailableState
          description="A tela de clientes já está pronta, mas o endpoint GET /clients ainda não está disponível no BFF. Assim que o Client Service for ativado, a listagem passará a funcionar sem alterações na interface."
          onRetry={() => void load(search)}
        />
      )}
      {status === "ready" && !items.length && (
        <EmptyState
          icon={Building2}
          title="Nenhum cliente cadastrado"
          description={search ? "Nenhum cliente encontrado para esta pesquisa." : "Cadastre o primeiro cliente para iniciar a operação mensal."}
        />
      )}
      {status === "ready" && Boolean(items.length) && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((client) => (
            <ThemeSurface key={client.id} className="p-5 transition hover:-translate-y-0.5 hover:border-border-strong">
              <div className="flex items-start justify-between gap-4">
                <span className="grid size-10 place-items-center rounded-xl border border-primary/15 bg-primary/7 text-primary"><Building2 className="size-4.5" /></span>
                <ClientStatusBadge status={client.status} />
              </div>
              <h2 className="mt-5 font-semibold text-white">{client.tradeName || client.name}</h2>
              {client.tradeName && <p className="mt-1 truncate text-xs text-muted">{client.name}</p>}
              <div className="mt-5 flex items-center justify-between border-t border-border pt-4 text-xs">
                <span className="font-mono text-muted">{client.cnpj}</span>
                <span className="flex items-center gap-1.5 text-muted"><MapPin className="size-3" /> {client.city ? `${client.city}${client.state ? `/${client.state}` : ""}` : "Sem cidade"}</span>
              </div>
            </ThemeSurface>
          ))}
        </div>
      )}

      {canCreate && (
        <FormDrawer
          open={drawerOpen}
          onClose={closeDrawer}
          title="Novo cliente"
          description="Os dados são enviados diretamente ao Client Service por meio do BFF. Nenhum cliente é salvo apenas neste dispositivo."
        >
          {status !== "unavailable" ? (
            <ClientForm onSubmit={handleCreate} submitting={submitting} generalError={formError} disabledReason={formUnavailable} />
          ) : (
            <ServiceUnavailableState description="O endpoint de criação de clientes ainda não está disponível no BFF. Nenhum cliente é salvo enquanto o serviço estiver ausente." />
          )}
        </FormDrawer>
      )}
    </div>
  );
}

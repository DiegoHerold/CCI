"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mail, Plus, UserRoundX, Users as UsersIcon } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { RoleBadge } from "@/components/badges/role-badge";
import { UserStatusBadge } from "@/components/badges/user-status-badge";
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
import { InviteUserForm } from "@/features/users/invite-user-form";
import { usersApi } from "@/lib/api/users-api";
import { clientsApi } from "@/lib/api/clients-api";
import { ApiError } from "@/lib/api/http-client";
import { classifyApiError, friendlyErrorMessage } from "@/lib/api/error-utils";
import type { ClientRecord, InviteUserPayload, UserRecord } from "@/types/api";

type PageStatus = "loading" | "ready" | "error" | "unavailable";

const RESENDABLE = new Set(["PENDING_INVITE", "INVITE_EXPIRED"]);

export default function UsersPage() {
  return <RequirePermission permission="users:read"><UsersContent /></RequirePermission>;
}

function UsersContent() {
  const { user } = useAuth();
  const [items, setItems] = useState<UserRecord[]>([]);
  const [status, setStatus] = useState<PageStatus>("loading");
  const [search, setSearch] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formUnavailable, setFormUnavailable] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [rowActionUnavailable, setRowActionUnavailable] = useState<string | null>(null);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [clientsUnavailable, setClientsUnavailable] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (searchTerm: string) => {
    setStatus("loading");
    try {
      const response = await usersApi.list({ search: searchTerm || undefined, limit: 50 });
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

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await clientsApi.list({ limit: 100 });
        if (active) setClients(response.items ?? []);
      } catch (error) {
        if (active && classifyApiError(error) === "SERVICE_UNAVAILABLE") setClientsUnavailable(true);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

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

  async function handleInvite(payload: InviteUserPayload) {
    setSubmitting(true);
    setFormError(null);
    setFormUnavailable(null);
    try {
      await usersApi.invite(payload);
      setDrawerOpen(false);
      setSuccessMessage(`Convite enviado para "${payload.email}".`);
      await load(search);
    } catch (error) {
      const code = classifyApiError(error);
      if (code === "SERVICE_UNAVAILABLE") {
        setFormUnavailable(
          "Convite ainda não disponível. A tela de convite está pronta, mas o endpoint de criação/envio de convite ainda não está disponível no BFF. Nenhum usuário foi criado e nenhum e-mail foi enviado.",
        );
        return;
      }
      const message = error instanceof ApiError
        ? friendlyErrorMessage(error, "Não foi possível enviar o convite. Confira os dados e tente novamente.")
        : "Não foi possível enviar o convite. Confira os dados e tente novamente.";
      setFormError(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend(targetUser: UserRecord) {
    setRowActionUnavailable(null);
    try {
      await usersApi.resendInvite(targetUser.id);
      setSuccessMessage(`Convite reenviado para "${targetUser.email}".`);
    } catch (error) {
      if (classifyApiError(error) === "SERVICE_UNAVAILABLE") {
        setRowActionUnavailable("O endpoint de reenvio de convite ainda não está disponível no BFF. Nenhum e-mail foi enviado.");
        return;
      }
      setRowActionUnavailable("Não foi possível reenviar o convite agora.");
    }
  }

  async function handleDisable(targetUser: UserRecord) {
    if (!window.confirm(`Desativar o usuário "${targetUser.name}"?`)) return;
    setRowActionUnavailable(null);
    try {
      await usersApi.disable(targetUser.id);
      setSuccessMessage(`Usuário "${targetUser.name}" desativado.`);
      await load(search);
    } catch (error) {
      if (classifyApiError(error) === "SERVICE_UNAVAILABLE") {
        setRowActionUnavailable("O endpoint de desativação de usuários ainda não está disponível no BFF.");
        return;
      }
      setRowActionUnavailable("Não foi possível desativar este usuário agora.");
    }
  }

  const canInvite = hasPermission(user, "users:create");
  const canUpdate = hasPermission(user, "users:update") || canInvite;
  const canDisable = hasPermission(user, "users:disable");
  const isAdmin = Boolean(user?.roles.includes("ADMIN"));

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Control Plane"
        title="Usuários"
        description="Contas administradas pelo Identity Service. Convites, roles e desativação passam sempre pelo BFF."
        action={canInvite ? (
          <Button onClick={openDrawer}>
            <Plus aria-hidden="true" /> Novo usuário
          </Button>
        ) : undefined}
      />

      {successMessage && <SuccessNotice message={successMessage} />}
      {rowActionUnavailable && <ServiceUnavailableState description={rowActionUnavailable} />}

      <DataToolbar
        searchValue={search}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Pesquisar por nome ou e-mail"
      />

      {status === "loading" && <LoadingState title="Carregando usuários" description="Consultando o Identity Service pelo BFF." />}
      {status === "error" && <ErrorState onRetry={() => void load(search)} />}
      {status === "unavailable" && (
        <ServiceUnavailableState
          description="A tela de usuários já está pronta, mas o endpoint GET /users ainda não está disponível no BFF."
          onRetry={() => void load(search)}
        />
      )}
      {status === "ready" && !items.length && (
        <EmptyState
          icon={UsersIcon}
          title="Nenhum usuário cadastrado"
          description={search ? "Nenhum usuário encontrado para esta pesquisa." : "Convide o primeiro usuário para iniciar a operação."}
        />
      )}
      {status === "ready" && Boolean(items.length) && (
        <ThemeSurface className="overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-white/[0.02] text-[0.68rem] uppercase tracking-[0.08em] text-muted">
              <tr>
                <th className="px-5 py-3 font-semibold">Usuário</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Roles</th>
                <th className="px-5 py-3 font-semibold text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-border/60 last:border-0">
                  <td className="px-5 py-4">
                    <p className="font-medium text-white">{item.name || "—"}</p>
                    <p className="mt-0.5 text-xs text-muted">{item.email}</p>
                  </td>
                  <td className="px-5 py-4"><UserStatusBadge status={item.status} /></td>
                  <td className="px-5 py-4">
                    <div className="flex flex-wrap gap-1.5">
                      {(item.roles ?? []).length ? item.roles.map((role) => <RoleBadge key={role} role={role} />) : <span className="text-xs text-muted">—</span>}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-2">
                      {canUpdate && RESENDABLE.has(item.status) && (
                        <Button variant="ghost" size="sm" onClick={() => void handleResend(item)}>
                          <Mail aria-hidden="true" /> Reenviar convite
                        </Button>
                      )}
                      {canDisable && item.status === "ACTIVE" && (
                        <Button variant="ghost" size="sm" onClick={() => void handleDisable(item)}>
                          <UserRoundX aria-hidden="true" /> Desativar
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ThemeSurface>
      )}

      {canInvite && (
        <FormDrawer
          open={drawerOpen}
          onClose={closeDrawer}
          title="Convidar usuário"
          description="O convite é enviado pelo backend por e-mail. Nenhuma senha é definida neste formulário."
        >
          <InviteUserForm
            onSubmit={handleInvite}
            submitting={submitting}
            generalError={formError}
            disabledReason={formUnavailable}
            allowAdminRole={isAdmin}
            clients={clients}
            clientsUnavailable={clientsUnavailable}
          />
        </FormDrawer>
      )}
    </div>
  );
}

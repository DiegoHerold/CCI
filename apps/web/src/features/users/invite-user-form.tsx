"use client";

import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormErrorState } from "@/components/states/form-error-state";
import { InlineFieldError } from "@/components/states/inline-field-error";
import { cn } from "@/lib/utils";
import type { ClientRecord, InviteUserPayload } from "@/types/api";

const GLOBAL_ROLES = ["ADMIN", "MANAGER", "OPERATOR", "VIEWER"] as const;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormValues {
  name: string;
  email: string;
  roles: string[];
  clientIds: string[];
}

type FieldErrors = Partial<Record<"name" | "email" | "roles", string>>;

function validate(values: FormValues): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.name.trim()) errors.name = "Informe o nome do usuário.";
  if (!values.email.trim()) {
    errors.email = "Informe o e-mail do usuário.";
  } else if (!EMAIL_PATTERN.test(values.email.trim())) {
    errors.email = "Informe um e-mail válido.";
  }
  if (!values.roles.length) errors.roles = "Selecione ao menos uma role global.";
  return errors;
}

export function InviteUserForm({
  onSubmit,
  submitting,
  generalError,
  disabledReason,
  allowAdminRole,
  clients,
  clientsUnavailable,
}: {
  onSubmit: (payload: InviteUserPayload) => Promise<void>;
  submitting: boolean;
  generalError: string | null;
  disabledReason?: string | null;
  allowAdminRole: boolean;
  clients: ClientRecord[];
  clientsUnavailable: boolean;
}) {
  const [values, setValues] = useState<FormValues>({ name: "", email: "", roles: ["OPERATOR"], clientIds: [] });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  function toggleRole(role: string) {
    setValues((current) => ({
      ...current,
      roles: current.roles.includes(role) ? current.roles.filter((item) => item !== role) : [...current.roles, role],
    }));
  }

  function toggleClient(clientId: string) {
    setValues((current) => ({
      ...current,
      clientIds: current.clientIds.includes(clientId)
        ? current.clientIds.filter((item) => item !== clientId)
        : [...current.clientIds, clientId],
    }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const payload: InviteUserPayload = {
      name: values.name.trim(),
      email: values.email.trim(),
      roles: values.roles,
    };
    if (values.clientIds.length) payload.clientIds = values.clientIds;

    await onSubmit(payload);
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <FormErrorState message={generalError} />

      <div className="space-y-2">
        <Label htmlFor="invite-name">Nome *</Label>
        <Input id="invite-name" value={values.name} onChange={(event) => setValues((current) => ({ ...current, name: event.target.value }))} placeholder="Nome do usuário" aria-invalid={Boolean(fieldErrors.name)} />
        <InlineFieldError message={fieldErrors.name} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="invite-email">E-mail *</Label>
        <Input id="invite-email" type="email" value={values.email} onChange={(event) => setValues((current) => ({ ...current, email: event.target.value }))} placeholder="usuario@empresa.com" aria-invalid={Boolean(fieldErrors.email)} />
        <InlineFieldError message={fieldErrors.email} />
      </div>

      <div className="space-y-2">
        <Label>Roles globais *</Label>
        <div className="flex flex-wrap gap-2">
          {GLOBAL_ROLES.map((role) => {
            const disabled = role === "ADMIN" && !allowAdminRole;
            const selected = values.roles.includes(role);
            return (
              <button
                key={role}
                type="button"
                disabled={disabled}
                onClick={() => toggleRole(role)}
                aria-pressed={selected}
                title={disabled ? "Apenas administradores podem atribuir a role ADMIN." : undefined}
                className={cn(
                  "rounded-lg border px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-40",
                  selected ? "border-primary/60 bg-primary/12 text-primary" : "border-border-strong bg-white/[0.03] text-muted-strong hover:border-white/25",
                )}
              >
                {role}
              </button>
            );
          })}
        </div>
        <InlineFieldError message={fieldErrors.roles} />
      </div>

      <div className="space-y-2">
        <Label>Vínculo com clientes (opcional)</Label>
        {clientsUnavailable ? (
          <p className="rounded-lg border border-border-strong bg-white/[0.02] p-3 text-xs leading-5 text-muted">
            Vínculo com clientes indisponível. O cadastro de clientes ainda não está ativo no BFF. Você poderá vincular usuários a clientes quando o Client Service estiver disponível.
          </p>
        ) : clients.length ? (
          <div className="max-h-40 space-y-1.5 overflow-y-auto rounded-lg border border-border-strong bg-black/15 p-2">
            {clients.map((client) => (
              <label key={client.id} className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm text-muted-strong hover:bg-white/[0.035]">
                <input type="checkbox" checked={values.clientIds.includes(client.id)} onChange={() => toggleClient(client.id)} className="size-3.5 rounded border-border-strong accent-primary" />
                {client.tradeName || client.name}
              </label>
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-border-strong bg-white/[0.02] p-3 text-xs leading-5 text-muted">
            Nenhum cliente cadastrado ainda. O convite pode ser enviado sem vínculo e o cliente pode ser associado depois.
          </p>
        )}
      </div>

      {disabledReason && <FormErrorState message={disabledReason} />}

      <Button type="submit" size="lg" disabled={submitting} className="w-full">
        {submitting ? <><LoaderCircle className="animate-spin" aria-hidden="true" /> Enviando convite…</> : "Enviar convite"}
      </Button>
      <p className="text-center text-[0.68rem] leading-5 text-muted/75">
        Nenhuma senha é definida aqui. O novo usuário define a própria senha ao aceitar o convite por e-mail.
      </p>
    </form>
  );
}

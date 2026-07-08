"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormErrorState } from "@/components/states/form-error-state";
import { InlineFieldError } from "@/components/states/inline-field-error";
import { formatCnpj, isValidCnpj, normalizeCnpjDigits } from "@/lib/validation/cnpj";
import type { CreateClientPayload } from "@/types/api";
import { LoaderCircle } from "lucide-react";

const TAX_REGIMES = [
  { value: "", label: "Não informado" },
  { value: "SIMPLES_NACIONAL", label: "Simples Nacional" },
  { value: "LUCRO_PRESUMIDO", label: "Lucro Presumido" },
  { value: "LUCRO_REAL", label: "Lucro Real" },
  { value: "MEI", label: "MEI" },
];

export interface ClientFormValues {
  code: string;
  name: string;
  tradeName: string;
  cnpj: string;
  taxRegime: string;
  city: string;
  state: string;
  defaultFolderPath: string;
  competenceFolderPattern: string;
  notes: string;
}

const emptyValues: ClientFormValues = {
  code: "",
  name: "",
  tradeName: "",
  cnpj: "",
  taxRegime: "",
  city: "",
  state: "",
  defaultFolderPath: "",
  competenceFolderPattern: "{{YYYY}}/{{MM}}",
  notes: "",
};

type FieldErrors = Partial<Record<keyof ClientFormValues, string>>;

function validate(values: ClientFormValues): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.name.trim()) errors.name = "Informe a razão social.";
  if (!values.cnpj.trim()) {
    errors.cnpj = "Informe o CNPJ.";
  } else if (!isValidCnpj(values.cnpj)) {
    errors.cnpj = "CNPJ inválido. Confira os dígitos verificadores.";
  }
  if (values.state && values.state.trim().length !== 2) errors.state = "Use a sigla da UF com 2 letras.";
  return errors;
}

export function ClientForm({
  onSubmit,
  submitting,
  generalError,
  disabledReason,
}: {
  onSubmit: (payload: CreateClientPayload) => Promise<void>;
  submitting: boolean;
  generalError: string | null;
  /** Quando preenchido, o formulário fica visível mas explica que o envio ainda depende do backend. */
  disabledReason?: string | null;
}) {
  const [values, setValues] = useState<ClientFormValues>(emptyValues);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  function update<K extends keyof ClientFormValues>(key: K, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const errors = validate(values);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const payload: CreateClientPayload = {
      name: values.name.trim(),
      cnpj: normalizeCnpjDigits(values.cnpj),
    };
    if (values.code.trim()) payload.code = values.code.trim();
    if (values.tradeName.trim()) payload.tradeName = values.tradeName.trim();
    if (values.taxRegime) payload.taxRegime = values.taxRegime;
    if (values.city.trim()) payload.city = values.city.trim();
    if (values.state.trim()) payload.state = values.state.trim().toUpperCase();
    if (values.defaultFolderPath.trim()) payload.defaultFolderPath = values.defaultFolderPath.trim();
    if (values.competenceFolderPattern.trim()) payload.competenceFolderPattern = values.competenceFolderPattern.trim();
    if (values.notes.trim()) payload.notes = values.notes.trim();

    await onSubmit(payload);
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <FormErrorState message={generalError} />

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="client-name">Razão social *</Label>
          <Input id="client-name" value={values.name} onChange={(event) => update("name", event.target.value)} placeholder="Empresa Exemplo LTDA" aria-invalid={Boolean(fieldErrors.name)} />
          <InlineFieldError message={fieldErrors.name} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-trade-name">Nome fantasia / apelido</Label>
          <Input id="client-trade-name" value={values.tradeName} onChange={(event) => update("tradeName", event.target.value)} placeholder="Empresa Exemplo" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-code">Código interno</Label>
          <Input id="client-code" value={values.code} onChange={(event) => update("code", event.target.value)} placeholder="0001" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-cnpj">CNPJ *</Label>
          <Input
            id="client-cnpj"
            value={values.cnpj}
            onChange={(event) => update("cnpj", formatCnpj(event.target.value))}
            placeholder="12.345.678/0001-95"
            inputMode="numeric"
            aria-invalid={Boolean(fieldErrors.cnpj)}
          />
          <InlineFieldError message={fieldErrors.cnpj} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-tax-regime">Regime tributário</Label>
          <select
            id="client-tax-regime"
            value={values.taxRegime}
            onChange={(event) => update("taxRegime", event.target.value)}
            className="h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3.5 text-sm text-foreground shadow-inner shadow-black/10 transition hover:border-white/25 focus:border-primary/70 focus:ring-3 focus:ring-primary/10"
          >
            {TAX_REGIMES.map((regime) => <option key={regime.value} value={regime.value}>{regime.label}</option>)}
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-city">Cidade</Label>
          <Input id="client-city" value={values.city} onChange={(event) => update("city", event.target.value)} placeholder="Gravataí" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-state">UF</Label>
          <Input id="client-state" value={values.state} onChange={(event) => update("state", event.target.value.toUpperCase())} placeholder="RS" maxLength={2} aria-invalid={Boolean(fieldErrors.state)} />
          <InlineFieldError message={fieldErrors.state} />
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="client-folder">Pasta padrão</Label>
          <Input id="client-folder" value={values.defaultFolderPath} onChange={(event) => update("defaultFolderPath", event.target.value)} placeholder="R:\Clientes\Empresa Exemplo" />
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="client-folder-pattern">Padrão de pasta por competência</Label>
          <Input id="client-folder-pattern" value={values.competenceFolderPattern} onChange={(event) => update("competenceFolderPattern", event.target.value)} placeholder="{{YYYY}}/{{MM}}" />
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="client-notes">Observações</Label>
          <textarea
            id="client-notes"
            value={values.notes}
            onChange={(event) => update("notes", event.target.value)}
            rows={3}
            placeholder="Cliente com fechamento mensal recorrente."
            className="w-full rounded-lg border border-border-strong bg-black/20 px-3.5 py-2.5 text-sm text-foreground shadow-inner shadow-black/10 transition placeholder:text-muted/65 hover:border-white/25 focus:border-primary/70 focus:ring-3 focus:ring-primary/10"
          />
        </div>
      </div>

      {disabledReason && <FormErrorState message={disabledReason} />}

      <Button type="submit" size="lg" disabled={submitting} className="w-full">
        {submitting ? <><LoaderCircle className="animate-spin" aria-hidden="true" /> Enviando…</> : "Cadastrar cliente"}
      </Button>
    </form>
  );
}

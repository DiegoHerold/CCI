"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, ArrowRight, CheckCircle2, LoaderCircle, LockKeyhole, ShieldAlert, ShieldCheck } from "lucide-react";
import { ProductLogo } from "@/components/brand/product-logo";
import { ServiceUnavailableState } from "@/components/states/service-unavailable-state";
import { LoadingState } from "@/components/states/loading-state";
import { EmptyState } from "@/components/states/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth-api";
import { classifyApiError } from "@/lib/api/error-utils";
import type { InvitationDetails } from "@/types/api";

const PASSWORD_PATTERN = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

type ValidationState = "loading" | "valid" | "invalid" | "expired" | "unavailable" | "error";

export default function AcceptInvitePage() {
  return (
    <main className="cci-grid cci-noise relative flex min-h-screen items-center justify-center overflow-hidden p-5 sm:p-8">
      <div className="absolute left-[18%] top-[-12rem] size-[32rem] rounded-full bg-primary/[0.075] blur-[100px]" />
      <div className="absolute bottom-[-15rem] right-[-8rem] size-[34rem] rounded-full bg-violet/[0.07] blur-[110px]" />
      <div className="relative w-full max-w-md">
        <div className="mb-8 flex justify-center"><ProductLogo /></div>
        <div className="glass-panel relative overflow-hidden rounded-2xl p-6 sm:p-8">
          <div className="absolute inset-x-12 top-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent" />
          <Suspense fallback={<LoadingState title="Validando convite" description="Consultando o token com o BFF." />}>
            <AcceptInviteContent />
          </Suspense>
        </div>
      </div>
    </main>
  );
}

function AcceptInviteContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") ?? "";

  const [state, setState] = useState<ValidationState>("loading");
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    let active = true;
    const timeout = window.setTimeout(() => {
      if (!token) {
        if (active) setState("invalid");
        return;
      }
      (async () => {
        try {
          const details = await authApi.getInvitation(token);
          if (!active) return;
          if (details.status === "EXPIRED") {
            setState("expired");
          } else if (details.status === "INVALID") {
            setState("invalid");
          } else {
            setInvitation(details);
            setState("valid");
          }
        } catch (error) {
          if (!active) return;
          setState(classifyApiError(error) === "SERVICE_UNAVAILABLE" ? "unavailable" : "error");
        }
      })();
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [token]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFieldError(null);
    setSubmitError(null);

    if (!PASSWORD_PATTERN.test(password)) {
      setFieldError("A senha deve ter ao menos 8 caracteres, incluindo uma letra e um número.");
      return;
    }
    if (password !== confirmPassword) {
      setFieldError("As senhas informadas não coincidem.");
      return;
    }

    setSubmitting(true);
    try {
      await authApi.acceptInvitation(token, { password, confirmPassword });
      setAccepted(true);
      setTimeout(() => router.replace("/login"), 1600);
    } catch (error) {
      if (classifyApiError(error) === "SERVICE_UNAVAILABLE") {
        setSubmitError(
          "Aceite de convite ainda não disponível. O link foi reconhecido pela interface, mas o serviço de convite ainda não está disponível no BFF. Tente novamente quando o módulo de identidade estiver ativo.",
        );
        return;
      }
      setSubmitError("Não foi possível confirmar o convite. Verifique os dados e tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  if (state === "loading") {
    return <LoadingState title="Validando convite" description="Consultando o token com o BFF." />;
  }

  if (state === "unavailable") {
    return (
      <ServiceUnavailableState
        title="Aceite de convite ainda não disponível"
        description="O link foi reconhecido pela interface, mas o serviço de convite ainda não está disponível no BFF. Tente novamente quando o módulo de identidade estiver ativo."
      />
    );
  }

  if (state === "invalid") {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="Convite inválido"
        description="Este link de convite não é válido. Solicite um novo convite a um administrador."
      />
    );
  }

  if (state === "expired") {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="Convite expirado"
        description="Este convite expirou. Solicite a um administrador que envie um novo convite."
      />
    );
  }

  if (state === "error") {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="Não foi possível validar o convite"
        description="Ocorreu um erro inesperado ao validar o token. Tente novamente em instantes."
      />
    );
  }

  if (accepted) {
    return (
      <div className="flex flex-col items-center gap-4 py-4 text-center">
        <span className="grid size-12 place-items-center rounded-xl border border-success/20 bg-success/8 text-success"><CheckCircle2 className="size-5" /></span>
        <h2 className="text-xl font-semibold text-white">Conta ativada</h2>
        <p className="text-sm leading-6 text-muted">Sua senha foi definida. Redirecionando para o login…</p>
      </div>
    );
  }

  return (
    <>
      <span className="mb-6 grid size-11 place-items-center rounded-xl border border-primary/20 bg-primary/8 text-primary">
        <ShieldCheck className="size-5" aria-hidden="true" />
      </span>
      <p className="text-xs font-semibold uppercase tracking-[0.17em] text-primary">Convite CCI</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-white">Defina sua senha</h2>
      <p className="mb-7 mt-2 text-sm leading-6 text-muted">
        {invitation ? <>Convite para <strong className="text-foreground">{invitation.name}</strong> ({invitation.email}).</> : "Defina a senha da sua nova conta."}
      </p>

      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="space-y-2">
          <Label htmlFor="new-password">Nova senha</Label>
          <div className="relative">
            <LockKeyhole className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-muted" aria-hidden="true" />
            <Input id="new-password" type="password" autoComplete="new-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Mínimo 8 caracteres, letra e número" className="pl-10" />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm-password">Confirmar senha</Label>
          <div className="relative">
            <LockKeyhole className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-muted" aria-hidden="true" />
            <Input id="confirm-password" type="password" autoComplete="new-password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Repita a senha" className="pl-10" />
          </div>
        </div>

        {fieldError && (
          <div role="alert" className="flex gap-2.5 rounded-lg border border-danger/20 bg-danger/[0.065] p-3 text-sm leading-5 text-danger">
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {fieldError}
          </div>
        )}
        {submitError && (
          <div role="alert" className="flex gap-2.5 rounded-lg border border-danger/20 bg-danger/[0.065] p-3 text-sm leading-5 text-danger">
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {submitError}
          </div>
        )}

        <Button type="submit" size="lg" disabled={submitting} className="group w-full">
          {submitting ? <><LoaderCircle className="animate-spin" aria-hidden="true" /> Confirmando…</> : <>Ativar minha conta <ArrowRight className="transition-transform group-hover:translate-x-0.5" aria-hidden="true" /></>}
        </Button>
        <p className="text-center text-[0.68rem] leading-5 text-muted/75">
          Sua senha nunca é registrada em log. Após ativar, você será redirecionado para o login.
        </p>
      </form>
    </>
  );
}

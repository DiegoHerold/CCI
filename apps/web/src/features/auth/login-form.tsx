"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, ArrowRight, LoaderCircle, LockKeyhole, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "./auth-provider";
import { ApiError } from "@/lib/api/http-client";

function loginError(error: unknown) {
  if (!(error instanceof ApiError)) return "Não foi possível entrar agora. Tente novamente.";
  if (error.status === 401) return "E-mail ou senha inválidos.";
  if (error.status === 423 || error.code === "ACCOUNT_LOCKED") return "Acesso temporariamente bloqueado. Tente novamente mais tarde.";
  if (error.status === 429) return "Muitas tentativas. Aguarde um instante antes de tentar novamente.";
  if (error.status === 0 || error.status === 503) return "Não foi possível conectar ao BFF. Verifique se a plataforma está disponível.";
  return "Não foi possível entrar agora. Tente novamente.";
}

export function LoginForm() {
  const { login, status } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard");
  }, [router, status]);

  return (
    <form
      className="space-y-5"
      onSubmit={async (event) => {
        event.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
          await login({ email: email.trim(), password });
          const destination = searchParams.get("next");
          router.replace(destination?.startsWith("/") ? destination : "/dashboard");
        } catch (reason) {
          setError(loginError(reason));
        } finally {
          setSubmitting(false);
        }
      }}
    >
      <div className="space-y-2">
        <Label htmlFor="email">E-mail</Label>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-muted" aria-hidden="true" />
          <Input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="voce@escritorio.com.br" className="pl-10" aria-describedby={error ? "login-error" : undefined} />
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Senha</Label>
          <span className="text-[0.68rem] text-muted">Acesso protegido</span>
        </div>
        <div className="relative">
          <LockKeyhole className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-muted" aria-hidden="true" />
          <Input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Sua senha" className="pl-10" aria-describedby={error ? "login-error" : undefined} />
        </div>
      </div>

      {error && (
        <div id="login-error" role="alert" className="flex gap-2.5 rounded-lg border border-danger/20 bg-danger/[0.065] p-3 text-sm leading-5 text-danger">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {error}
        </div>
      )}

      <Button type="submit" size="lg" disabled={submitting || status === "loading"} className="group w-full">
        {submitting ? <><LoaderCircle className="animate-spin" aria-hidden="true" /> Validando acesso…</> : <>Entrar no cockpit <ArrowRight className="transition-transform group-hover:translate-x-0.5" aria-hidden="true" /></>}
      </Button>
      <p className="text-center text-[0.68rem] leading-5 text-muted/75">
        Sua sessão é validada pelo BFF. Nenhuma credencial é armazenada neste dispositivo.
      </p>
    </form>
  );
}

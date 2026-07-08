"use client";

import { Suspense } from "react";
import { ArrowUpRight, Binary, FileCheck2, Fingerprint, GitCompareArrows, ShieldCheck } from "lucide-react";
import { ProductLogo } from "@/components/brand/product-logo";
import { Badge } from "@/components/ui/badge";
import { LoginForm } from "@/features/auth/login-form";

const flow = [
  { label: "Documento", icon: FileCheck2 },
  { label: "Variáveis", icon: Binary },
  { label: "Regras", icon: GitCompareArrows },
  { label: "Auditoria", icon: Fingerprint },
];

export default function LoginPage() {
  return (
    <main className="cci-grid cci-noise relative min-h-screen overflow-hidden">
      <div className="absolute left-[18%] top-[-12rem] size-[32rem] rounded-full bg-primary/[0.075] blur-[100px]" />
      <div className="absolute bottom-[-15rem] right-[-8rem] size-[34rem] rounded-full bg-violet/[0.07] blur-[110px]" />
      <div className="relative mx-auto grid min-h-screen max-w-[92rem] items-stretch lg:grid-cols-[1.15fr_.85fr]">
        <section className="hidden flex-col justify-between px-10 py-10 lg:flex xl:px-16 xl:py-14">
          <ProductLogo />
          <div className="max-w-2xl pb-8">
            <Badge variant="info" className="mb-6 uppercase"><span className="size-1.5 rounded-full bg-primary animate-cci-pulse" /> Operação com rastreabilidade</Badge>
            <h1 className="max-w-xl text-[3.6rem] font-semibold leading-[1.03] tracking-[-0.055em] text-white xl:text-[4.4rem]">
              Conferência que deixa <span className="bg-gradient-to-r from-primary to-violet bg-clip-text text-transparent">rastro.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-muted-strong">
              Automatize conferências por cliente e competência com variáveis confirmadas, evidências e auditoria compreensível.
            </p>
            <div className="mt-10 grid grid-cols-4 gap-2">
              {flow.map(({ label, icon: Icon }, index) => (
                <div key={label} className="group relative rounded-xl border border-white/[0.08] bg-white/[0.025] p-3.5 transition hover:border-primary/20 hover:bg-primary/[0.035]">
                  {index < flow.length - 1 && <ArrowUpRight className="absolute -right-3 top-1/2 z-10 size-3.5 -translate-y-1/2 rotate-45 text-muted/50" aria-hidden="true" />}
                  <Icon className="size-4.5 text-primary/85" aria-hidden="true" />
                  <p className="mt-5 text-[0.67rem] font-semibold uppercase tracking-[0.12em] text-muted-strong">{label}</p>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted/60">Control Plane organiza. Auditoria gera confiança.</p>
        </section>

        <section className="flex min-h-screen items-center justify-center border-white/8 p-5 lg:border-l lg:bg-black/10 sm:p-8">
          <div className="w-full max-w-md">
            <div className="mb-8 flex justify-center lg:hidden"><ProductLogo /></div>
            <div className="glass-panel relative overflow-hidden rounded-2xl p-6 sm:p-8">
              <div className="absolute inset-x-12 top-0 h-px bg-gradient-to-r from-transparent via-primary/70 to-transparent" />
              <span className="mb-6 grid size-11 place-items-center rounded-xl border border-primary/20 bg-primary/8 text-primary">
                <ShieldCheck className="size-5" aria-hidden="true" />
              </span>
              <p className="text-xs font-semibold uppercase tracking-[0.17em] text-primary">Acesso CCI</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-white">Entre na central de conferência</h2>
              <p className="mb-7 mt-2 text-sm leading-6 text-muted">Use as credenciais administradas pelo Identity Service.</p>
              <Suspense fallback={<div className="h-72 animate-pulse rounded-xl bg-white/[0.03]" />}>
                <LoginForm />
              </Suspense>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

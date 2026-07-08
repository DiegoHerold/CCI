"use client";

import { Activity, Building2, CalendarDays, FileStack, FolderClock, ScrollText, ShieldCheck, Workflow } from "lucide-react";
import { ModuleCard } from "@/components/dashboard/module-card";
import { MetricCard } from "@/components/dashboard/metric-card";
import { TimelinePreview } from "@/components/dashboard/timeline-preview";
import { PageHeader } from "@/components/layout/page-header";
import { ThemeSurface } from "@/components/layout/theme-surface";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth/auth-provider";
import { formatCompetence } from "@/features/context/competence-selector";
import { useOperationalContext } from "@/features/context/operational-context-provider";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, selectedClient, status, reload } = useOperationalContext();
  const firstName = user?.name?.split(" ")[0] || "Usuário";

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Cockpit operacional" title={`Olá, ${firstName}.`} description="Acompanhe o contexto mensal e a base do fluxo de conferência sem métricas inventadas." />

      {status === "error" && <ErrorState onRetry={() => void reload()} />}
      {status === "loading" && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-44 rounded-xl" />)}
        </div>
      )}

      {status === "ready" && !data?.clients.length && (
        <EmptyState icon={Building2} title="Nenhum cliente vinculado" description="Você ainda não possui acesso a clientes. Solicite a um administrador que vincule seu usuário a um cliente." />
      )}

      {status === "ready" && Boolean(data?.clients.length) && !selectedClient && (
        <EmptyState icon={Building2} title="Selecione o contexto de trabalho" description="Escolha um cliente no seletor superior. A preferência será salva no BFF e usada para organizar a operação mensal." />
      )}

      {status === "ready" && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <MetricCard icon={Building2} label="Clientes acessíveis" value={data?.clients.length ?? 0} description="Retornados pelo contexto autorizado do BFF." />
          <MetricCard icon={CalendarDays} label="Competência atual" value={selectedClient ? formatCompetence(data?.currentCompetence.period) : "—"} description={selectedClient ? "Referência informada pelo Client Service." : "Nenhum cliente selecionado."} accent="violet" />
          <MetricCard icon={FileStack} label="Documentos esperados" value="—" description="Aguardando integração com modelos e ingestão." accent="primary" />
          <MetricCard icon={FolderClock} label="Pendências" value="—" description="Sem resultados reais disponíveis nesta fase." accent="warning" />
          <MetricCard icon={Activity} label="Execuções" value="—" description="O controle de execução será integrado depois." accent="success" />
          <MetricCard icon={ScrollText} label="Relatórios" value="—" description="Nenhum relatório foi produzido nesta fase." accent="violet" />
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(18rem,.5fr)]">
        <TimelinePreview ready={Boolean(selectedClient)} />
        <ThemeSurface className="p-5 sm:p-6">
          <p className="text-sm font-semibold text-white">Integridade do contexto</p>
          <div className="mt-5 space-y-4">
            {[
              ["Sessão autenticada", Boolean(user), "Identity Service"],
              ["Cliente autorizado", Boolean(selectedClient), selectedClient?.tradeName || selectedClient?.name || "Não selecionado"],
              ["Competência de referência", Boolean(selectedClient && data?.currentCompetence), selectedClient ? formatCompetence(data?.currentCompetence.period) : "Não selecionada"],
            ].map(([label, ok, detail]) => (
              <div key={String(label)} className="flex items-center gap-3">
                <span className={`grid size-8 place-items-center rounded-lg border ${ok ? "border-success/15 bg-success/7 text-success" : "border-white/8 bg-white/[0.025] text-muted"}`}><ShieldCheck className="size-3.5" /></span>
                <div className="min-w-0"><p className="text-xs font-medium text-foreground">{label}</p><p className="mt-0.5 truncate text-[0.68rem] text-muted">{detail}</p></div>
              </div>
            ))}
          </div>
        </ThemeSurface>
      </div>

      <section>
        <div className="mb-4 flex items-end justify-between"><div><h2 className="text-base font-semibold text-white">Próximos módulos</h2><p className="mt-1 text-xs text-muted">A arquitetura visual já reserva o fluxo completo.</p></div></div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <ModuleCard icon={FileStack} title="Mapa de documentos" description="Identificação, ausências, duplicidades e ambiguidades." phase="Data Plane" />
          <ModuleCard icon={Workflow} title="Regras versionadas" description="Conferências consumindo apenas variáveis confirmadas." phase="Control Plane" />
          <ModuleCard icon={Activity} title="Execuções" description="Workflows duráveis, reprocessamento e resultados." phase="Temporal" />
          <ModuleCard icon={ScrollText} title="Auditoria e relatórios" description="Evidências explicáveis e saídas exportáveis." phase="Saída" />
        </div>
      </section>
    </div>
  );
}

import { CheckCircle2, CircleDashed, FileSearch, Fingerprint, GitCompareArrows, Variable } from "lucide-react";
import { ThemeSurface } from "@/components/layout/theme-surface";

const stages = [
  { label: "Documentos", icon: FileSearch },
  { label: "Variáveis", icon: Variable },
  { label: "Regras", icon: GitCompareArrows },
  { label: "Auditoria", icon: Fingerprint },
];

export function TimelinePreview({ ready }: { ready: boolean }) {
  return (
    <ThemeSurface className="p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-white">Linha operacional</p>
          <p className="mt-1 text-xs text-muted">Fluxo preparado para a competência selecionada.</p>
        </div>
        {ready ? <CheckCircle2 className="size-4 text-success" aria-label="Contexto pronto" /> : <CircleDashed className="size-4 text-muted" aria-label="Aguardando contexto" />}
      </div>
      <div className="mt-7 grid grid-cols-4">
        {stages.map(({ label, icon: Icon }, index) => (
          <div key={label} className="relative flex flex-col items-center text-center">
            {index > 0 && <span className="absolute right-1/2 top-4 h-px w-full bg-gradient-to-r from-border-strong to-border" />}
            <span className="relative z-10 grid size-8 place-items-center rounded-full border border-border-strong bg-[#0d1521] text-muted"><Icon className="size-3.5" aria-hidden="true" /></span>
            <span className="mt-2 text-[0.62rem] font-medium text-muted sm:text-xs">{label}</span>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg border border-dashed border-border-strong bg-black/10 px-4 py-3 text-center text-xs text-muted">
        {ready ? "Aguardando documentos reais para iniciar o fluxo." : "Selecione um cliente para preparar o fluxo mensal."}
      </div>
    </ThemeSurface>
  );
}

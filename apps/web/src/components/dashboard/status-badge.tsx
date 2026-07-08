import { Badge } from "@/components/ui/badge";

const variants = {
  ativo: "success", inativo: "neutral", aberto: "info", fechado: "neutral", arquivado: "neutral",
  pendente: "warning", "em processamento": "info", aprovado: "success", divergente: "danger", erro: "danger", "revisão necessária": "warning",
} as const;

export function StatusBadge({ status }: { status: keyof typeof variants }) {
  return <Badge variant={variants[status]}><span className="size-1.5 rounded-full bg-current" /> {status}</Badge>;
}

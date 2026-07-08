import { Badge } from "@/components/ui/badge";
import type { ClientStatus } from "@/types/api";

const labels: Record<ClientStatus, { label: string; variant: "success" | "neutral" | "warning" }> = {
  ACTIVE: { label: "Ativo", variant: "success" },
  INACTIVE: { label: "Inativo", variant: "neutral" },
  ARCHIVED: { label: "Arquivado", variant: "neutral" },
};

export function ClientStatusBadge({ status }: { status: ClientStatus | string }) {
  const entry = labels[status as ClientStatus] ?? { label: status, variant: "neutral" as const };
  return <Badge variant={entry.variant}><span className="size-1.5 rounded-full bg-current" /> {entry.label}</Badge>;
}

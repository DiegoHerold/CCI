import { Badge } from "@/components/ui/badge";
import type { UserStatus } from "@/types/api";

const labels: Record<UserStatus, { label: string; variant: "success" | "neutral" | "warning" | "danger" | "info" }> = {
  ACTIVE: { label: "Ativo", variant: "success" },
  INACTIVE: { label: "Inativo", variant: "neutral" },
  PENDING_INVITE: { label: "Convite pendente", variant: "info" },
  INVITE_EXPIRED: { label: "Convite expirado", variant: "warning" },
  BLOCKED: { label: "Bloqueado", variant: "danger" },
};

export function UserStatusBadge({ status }: { status: UserStatus | string }) {
  const entry = labels[status as UserStatus] ?? { label: status, variant: "neutral" as const };
  return <Badge variant={entry.variant}><span className="size-1.5 rounded-full bg-current" /> {entry.label}</Badge>;
}

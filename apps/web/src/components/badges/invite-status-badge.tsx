import { Badge } from "@/components/ui/badge";

export function InviteStatusBadge({ sentAt, acceptedAt }: { sentAt?: string | null; acceptedAt?: string | null }) {
  if (acceptedAt) return <Badge variant="success"><span className="size-1.5 rounded-full bg-current" /> Convite aceito</Badge>;
  if (sentAt) return <Badge variant="info"><span className="size-1.5 rounded-full bg-current" /> Convite enviado</Badge>;
  return <Badge variant="neutral">Convite não enviado</Badge>;
}

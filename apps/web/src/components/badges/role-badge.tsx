import { Badge } from "@/components/ui/badge";

export function RoleBadge({ role }: { role: string }) {
  return <Badge variant="violet">{role}</Badge>;
}

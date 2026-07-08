import { ShieldX } from "lucide-react";
import { EmptyState } from "./empty-state";

export function ForbiddenState() {
  return (
    <EmptyState
      icon={ShieldX}
      title="Sem permissão para esta área"
      description="Seu perfil não possui a permissão necessária. O BFF continuará sendo a autoridade final de acesso; solicite a revisão do seu perfil a um administrador."
    />
  );
}

"use client";

import { PlugZap, RotateCcw } from "lucide-react";
import { EmptyState } from "./empty-state";
import { Button } from "@/components/ui/button";

export function ServiceUnavailableState({
  title = "Serviço ainda não disponível",
  description = "Esta tela já está preparada no frontend, mas o endpoint necessário ainda não está disponível no BFF. Quando o serviço for ativado, esta funcionalidade passará a funcionar sem alterar a interface.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      icon={PlugZap}
      title={title}
      description={description}
      action={onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          <RotateCcw aria-hidden="true" /> Tentar novamente
        </Button>
      ) : undefined}
    />
  );
}

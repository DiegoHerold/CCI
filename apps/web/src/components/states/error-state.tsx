"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";
import { EmptyState } from "./empty-state";
import { Button } from "@/components/ui/button";

export function ErrorState({
  title = "Não foi possível carregar os dados",
  description = "A conexão com o BFF ou um serviço dependente não está disponível agora.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      icon={AlertTriangle}
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

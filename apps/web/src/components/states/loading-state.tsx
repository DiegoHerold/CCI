"use client";

import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function LoadingState({
  title = "Preparando seu cockpit",
  description = "Validando sessão e carregando o contexto operacional.",
  fullScreen = false,
}: {
  title?: string;
  description?: string;
  fullScreen?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex min-h-56 items-center justify-center p-8",
        fullScreen && "cci-grid min-h-screen",
      )}
      role="status"
      aria-live="polite"
    >
      <div className="text-center">
        <span className="mx-auto mb-4 grid size-11 place-items-center rounded-xl border border-primary/20 bg-primary/8 text-primary">
          <LoaderCircle className="size-5 animate-spin" aria-hidden="true" />
        </span>
        <p className="font-semibold text-white">{title}</p>
        <p className="mt-1.5 text-sm text-muted">{description}</p>
      </div>
    </div>
  );
}

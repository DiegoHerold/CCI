"use client";

import { ArrowUpRight, GitCompareArrows } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { TemplateVersion } from "../types/templateBuilder";

export function TemplateVersionPanel({
  activeVersion,
  draftVersion,
  onCreateDraft,
  onPublish,
  busy,
}: {
  activeVersion?: TemplateVersion | null;
  draftVersion?: TemplateVersion | null;
  onCreateDraft: () => void;
  onPublish: (versionId: string) => void;
  busy?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Badge variant={activeVersion ? "success" : "neutral"}>
        ativa {activeVersion ? `v${activeVersion.versionNumber}` : "nenhuma"}
      </Badge>
      <Badge variant={draftVersion ? "warning" : "neutral"}>
        draft {draftVersion ? `v${draftVersion.versionNumber}` : "nenhuma"}
      </Badge>
      <Button type="button" size="sm" variant="secondary" onClick={onCreateDraft} disabled={busy}>
        <GitCompareArrows aria-hidden="true" /> Criar draft
      </Button>
      <Button type="button" size="sm" onClick={() => draftVersion && onPublish(draftVersion.id)} disabled={busy || !draftVersion}>
        <ArrowUpRight aria-hidden="true" /> Publicar
      </Button>
    </div>
  );
}

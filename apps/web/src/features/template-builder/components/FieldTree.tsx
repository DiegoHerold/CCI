"use client";

import { Boxes, ChevronDown, ListChecks } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { FieldTreeNode, TemplateField } from "../types/templateBuilder";
import { buildFieldTree } from "../utils/fieldPath";

function NodeRow({
  node,
  selectedFieldId,
  onSelect,
}: {
  node: FieldTreeNode;
  selectedFieldId?: string | null;
  onSelect: (field: TemplateField) => void;
}) {
  const selected = node.field?.id === selectedFieldId;
  return (
    <li>
      <div className="flex items-center gap-2">
        <ChevronDown className={cn("size-3 text-muted", !node.children.length && "opacity-0")} aria-hidden="true" />
        {node.field ? (
          <button
            type="button"
            className={cn(
              "flex min-h-8 flex-1 items-center justify-between gap-3 rounded-md px-2 text-left text-sm text-muted-strong hover:bg-white/[0.055] hover:text-white",
              selected && "bg-primary/10 text-primary",
            )}
            onClick={() => onSelect(node.field!)}
          >
            <span className="truncate">{node.label}</span>
            <Badge className="shrink-0">{node.field.fieldType}</Badge>
          </button>
        ) : (
          <span className="flex min-h-8 flex-1 items-center gap-2 rounded-md px-2 text-sm font-semibold text-white">
            <Boxes className="size-3.5 text-primary" aria-hidden="true" /> {node.label}
          </span>
        )}
      </div>
      {node.children.length > 0 && (
        <ul className="ml-5 mt-1 space-y-1 border-l border-border pl-2">
          {node.children.map((child) => (
            <NodeRow key={child.key} node={child} selectedFieldId={selectedFieldId} onSelect={onSelect} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function FieldTree({
  fields,
  selectedFieldId,
  onSelect,
}: {
  fields: TemplateField[];
  selectedFieldId?: string | null;
  onSelect: (field: TemplateField) => void;
}) {
  const tree = buildFieldTree(fields);
  if (!tree.length) {
    return (
      <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted">
        Crie o primeiro campo para associar selecoes do documento.
      </div>
    );
  }
  return (
    <ul className="space-y-1">
      {tree.map((node) => (
        <NodeRow key={node.key} node={node} selectedFieldId={selectedFieldId} onSelect={onSelect} />
      ))}
    </ul>
  );
}

export function CreateFieldQuickActions({ onPick }: { onPick: (path: string) => void }) {
  const presets = ["empresa.cnpj", "periodo.competencia", "contas[]", "contas[].saldo_atual"];
  return (
    <div className="flex flex-wrap gap-2">
      <ListChecks className="mt-1 size-4 text-muted" aria-hidden="true" />
      {presets.map((path) => (
        <Button key={path} type="button" size="sm" variant="ghost" onClick={() => onPick(path)}>
          {path}
        </Button>
      ))}
    </div>
  );
}

"use client";

import { Eraser } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { TemplateAnnotation, TemplateField } from "../types/templateBuilder";

export function AnnotationList({
  annotations,
  fields,
  onDelete,
}: {
  annotations: TemplateAnnotation[];
  fields: TemplateField[];
  onDelete: (annotationId: string) => void;
}) {
  if (!annotations.length) {
    return <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted">Nenhuma annotation salva para este template.</p>;
  }
  return (
    <div className="space-y-2">
      {annotations.map((annotation) => {
        const field = fields.find((item) => item.id === annotation.fieldId);
        return (
          <div key={annotation.id} className="flex items-start justify-between gap-3 rounded-lg border border-border bg-black/12 p-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="info">{annotation.annotationType}</Badge>
                <span className="truncate text-sm font-semibold text-white">{field?.fieldPath ?? annotation.fieldId}</span>
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-muted">{annotation.selectedText || annotation.documentId}</p>
            </div>
            <Button type="button" size="icon" variant="ghost" aria-label="Remover annotation" onClick={() => onDelete(annotation.id)}>
              <Eraser aria-hidden="true" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { FieldType } from "../types/templateBuilder";
import { defaultLabelFromPath } from "../utils/fieldPath";
import { CreateFieldQuickActions } from "./FieldTree";

const FIELD_TYPES: FieldType[] = ["text", "number", "money", "date", "month", "cnpj", "cpf", "boolean", "object", "array", "table", "calculated", "unknown"];

export function FieldEditor({
  fieldPath,
  fieldType,
  onFieldPathChange,
  onFieldTypeChange,
  onSubmit,
  busy,
}: {
  fieldPath: string;
  fieldType: FieldType;
  onFieldPathChange: (value: string) => void;
  onFieldTypeChange: (value: FieldType) => void;
  onSubmit: () => void;
  busy?: boolean;
}) {
  return (
    <div className="space-y-3 rounded-lg border border-border bg-black/12 p-3">
      <div className="grid gap-3 sm:grid-cols-[1fr_150px]">
        <div className="space-y-1.5">
          <Label htmlFor="field-path">Campo/objeto</Label>
          <Input
            id="field-path"
            value={fieldPath}
            placeholder="empresa.cnpj"
            onChange={(event) => onFieldPathChange(event.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="field-type">Tipo</Label>
          <select
            id="field-type"
            className="h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3 text-sm text-foreground"
            value={fieldType}
            onChange={(event) => onFieldTypeChange(event.target.value as FieldType)}
          >
            {FIELD_TYPES.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>
      </div>
      <CreateFieldQuickActions onPick={(path) => {
        onFieldPathChange(path);
        if (path.endsWith("[]")) onFieldTypeChange("array");
      }} />
      <Button type="button" size="sm" onClick={onSubmit} disabled={busy || !fieldPath.trim()}>
        <Plus aria-hidden="true" /> Criar {fieldPath ? defaultLabelFromPath(fieldPath) : "campo"}
      </Button>
    </div>
  );
}

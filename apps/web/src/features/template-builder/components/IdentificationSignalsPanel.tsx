"use client";

import { Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { IdentificationSignal } from "../types/templateBuilder";

const SIGNAL_TYPES = ["contains_text", "contains_all_text", "sheet_name", "column_header", "has_cnpj", "has_currency_values", "structure_hint"];

export function IdentificationSignalsPanel({
  signals,
  signalType,
  signalValue,
  onSignalTypeChange,
  onSignalValueChange,
  onCreate,
  busy,
}: {
  signals: IdentificationSignal[];
  signalType: string;
  signalValue: string;
  onSignalTypeChange: (value: string) => void;
  onSignalValueChange: (value: string) => void;
  onCreate: () => void;
  busy?: boolean;
}) {
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-[180px_1fr_auto]">
        <div className="space-y-1.5">
          <Label htmlFor="signal-type">Sinal</Label>
          <select
            id="signal-type"
            className="h-10 w-full rounded-lg border border-border-strong bg-black/20 px-3 text-sm text-foreground"
            value={signalType}
            onChange={(event) => onSignalTypeChange(event.target.value)}
          >
            {SIGNAL_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="signal-value">Valor</Label>
          <Input id="signal-value" value={signalValue} placeholder="Balancete" onChange={(event) => onSignalValueChange(event.target.value)} />
        </div>
        <Button type="button" className="self-end" size="sm" onClick={onCreate} disabled={busy || !signalValue.trim()}>
          <Plus aria-hidden="true" /> Adicionar
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {signals.map((signal) => (
          <Badge key={signal.id} variant={signal.required ? "warning" : "neutral"}>
            {signal.signalType}: {signal.value}
          </Badge>
        ))}
        {!signals.length && <span className="text-sm text-muted">Nenhum sinal cadastrado.</span>}
      </div>
    </div>
  );
}

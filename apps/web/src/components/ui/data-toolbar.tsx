"use client";

import { Search } from "lucide-react";
import { Input } from "./input";

export function DataToolbar({
  searchValue,
  onSearchChange,
  searchPlaceholder = "Pesquisar…",
  action,
}: {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="relative w-full max-w-sm">
        <Search className="pointer-events-none absolute left-3.5 top-3.5 size-4 text-muted" aria-hidden="true" />
        <Input
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={searchPlaceholder}
          className="pl-10"
          aria-label={searchPlaceholder}
        />
      </div>
      {action}
    </div>
  );
}

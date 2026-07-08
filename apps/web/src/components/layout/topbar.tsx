"use client";

import { Menu, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ClientSelector } from "@/features/context/client-selector";
import { CompetenceSelector } from "@/features/context/competence-selector";
import { UserMenu } from "./user-menu";

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex h-[4.5rem] items-center gap-3 border-b border-border bg-[#080d15]/80 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenMenu} aria-label="Abrir navegação">
        <Menu aria-hidden="true" />
      </Button>
      <div className="hidden items-center gap-2 text-xs text-muted lg:flex">
        <Radio className="size-3.5 text-success" aria-hidden="true" />
        <span>Ambiente operacional</span>
      </div>
      <div className="ml-auto flex min-w-0 items-center gap-2.5">
        <ClientSelector />
        <CompetenceSelector />
        <UserMenu />
      </div>
    </header>
  );
}

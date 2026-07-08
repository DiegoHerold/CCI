"use client";

import { ChevronDown, LogOut, Settings2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/utils";

function initials(name?: string) {
  return name?.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "US";
}

export function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className="flex h-10 items-center gap-2 rounded-lg border border-border bg-white/[0.025] px-2 text-left transition hover:border-border-strong hover:bg-white/[0.05]"
      >
        <span className="grid size-7 place-items-center rounded-md bg-gradient-to-br from-primary/25 to-violet/20 text-[0.65rem] font-bold text-white">
          {initials(user?.name)}
        </span>
        <span className="hidden max-w-28 truncate text-xs font-semibold text-foreground xl:block">{user?.name}</span>
        <ChevronDown className={cn("size-3.5 text-muted transition", open && "rotate-180")} aria-hidden="true" />
      </button>

      {open && (
        <div role="menu" className="absolute right-0 top-12 z-50 w-64 rounded-xl border border-border-strong bg-[#0c131e] p-2 shadow-2xl shadow-black/50">
          <div className="border-b border-border px-2.5 py-2.5">
            <p className="truncate text-sm font-semibold text-white">{user?.name}</p>
            <p className="mt-0.5 truncate text-xs text-muted">{user?.email}</p>
          </div>
          <Link role="menuitem" href="/settings" onClick={() => setOpen(false)} className="mt-1 flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-muted-strong hover:bg-white/[0.05] hover:text-white">
            <Settings2 className="size-4" aria-hidden="true" /> Configurações
          </Link>
          <button
            role="menuitem"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try { await logout(); } finally { router.replace("/login"); }
            }}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-danger hover:bg-danger/8 disabled:opacity-50"
          >
            <LogOut className="size-4" aria-hidden="true" /> {busy ? "Encerrando…" : "Sair da sessão"}
          </button>
        </div>
      )}
    </div>
  );
}

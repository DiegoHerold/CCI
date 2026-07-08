"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { ProductLogo } from "@/components/brand/product-logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import { hasPermission } from "@/features/auth/permissions";
import { cn } from "@/lib/utils";
import { navigationGroups } from "./navigation";

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <>
      {open && <button aria-label="Fechar menu" className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[17rem] flex-col border-r border-border bg-[#080d15]/96 px-4 py-5 shadow-2xl shadow-black/30 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between px-1">
          <ProductLogo />
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose} aria-label="Fechar navegação">
            <X aria-hidden="true" />
          </Button>
        </div>

        <nav className="mt-8 flex-1 space-y-6 overflow-y-auto pr-1" aria-label="Navegação principal">
          {navigationGroups.map((group) => {
            const visibleItems = group.items.filter((item) => hasPermission(user, "permission" in item ? item.permission : undefined));
            if (!visibleItems.length) return null;
            return (
              <div key={group.label}>
                <p className="mb-2 px-3 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-muted/65">{group.label}</p>
                <ul className="space-y-1">
                  {visibleItems.map((item) => {
                    const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                    const Icon = item.icon;
                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          onClick={onClose}
                          className={cn(
                            "group flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted transition-all hover:bg-white/[0.045] hover:text-foreground",
                            active && "bg-primary/[0.075] text-white shadow-[inset_3px_0_0_var(--primary)]",
                          )}
                        >
                          <Icon className={cn("size-4.5 text-muted transition group-hover:text-primary", active && "text-primary")} aria-hidden="true" />
                          <span className="flex-1">{item.label}</span>
                          {"future" in item && item.future && <span className="size-1.5 rounded-full bg-white/15" title="Módulo futuro" />}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </nav>

        <div className="mt-5 rounded-xl border border-primary/10 bg-primary/[0.035] p-3.5">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-white">Control Plane</span>
            <Badge variant="success" className="px-2 py-0.5"><span className="size-1.5 rounded-full bg-success" /> Ativo</Badge>
          </div>
          <p className="mt-2 text-[0.68rem] leading-5 text-muted">Sessão, clientes e competências sob controle do BFF.</p>
        </div>
      </aside>
    </>
  );
}

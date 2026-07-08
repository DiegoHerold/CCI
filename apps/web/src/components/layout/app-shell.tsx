"use client";

import { useState } from "react";
import { OperationalContextProvider } from "@/features/context/operational-context-provider";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <OperationalContextProvider>
      <div className="min-h-screen bg-background">
        <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
        <div className="lg:pl-[17rem]">
          <Topbar onOpenMenu={() => setMenuOpen(true)} />
          <main className="mx-auto w-full max-w-[100rem] px-4 py-7 sm:px-6 sm:py-9 lg:px-8">
            {children}
          </main>
        </div>
      </div>
    </OperationalContextProvider>
  );
}

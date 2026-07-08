import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "./page";
import { AuthProvider } from "@/features/auth/auth-provider";
import { OperationalContextProvider } from "@/features/context/operational-context-provider";
import { __testing } from "@/lib/api/http-client";
import { authenticatedFetch, contextWithClient, contextWithoutClients } from "@/test/fixtures";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/dashboard",
}));

function renderDashboard(context = contextWithoutClients) {
  vi.stubGlobal("fetch", authenticatedFetch(context.user, context));
  return render(<AuthProvider><OperationalContextProvider><DashboardPage /></OperationalContextProvider></AuthProvider>);
}

describe("Dashboard", () => {
  beforeEach(() => __testing.reset());

  it("mostra estado específico quando não há clientes", async () => {
    renderDashboard();
    expect(await screen.findByText("Nenhum cliente vinculado")).toBeInTheDocument();
    expect(screen.getByText("Clientes acessíveis")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("mostra contexto real retornado pelo BFF", async () => {
    renderDashboard(contextWithClient);
    expect(await screen.findByText("Aurora")).toBeInTheDocument();
    expect(screen.getAllByText("07/2026").length).toBeGreaterThan(0);
    expect(screen.getByText("1")).toBeInTheDocument();
  });
});

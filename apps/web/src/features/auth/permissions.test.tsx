import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Sidebar } from "@/components/layout/sidebar";
import { ForbiddenState } from "@/components/states/forbidden-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { AuthProvider } from "./auth-provider";
import { RequirePermission } from "./require-permission";
import { __testing } from "@/lib/api/http-client";
import { adminUser, authenticatedFetch, user } from "@/test/fixtures";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/dashboard",
}));

describe("permissões e estados", () => {
  beforeEach(() => __testing.reset());

  it("esconde item de menu sem a permissão necessária", async () => {
    vi.stubGlobal("fetch", authenticatedFetch(user));
    render(<AuthProvider><Sidebar open onClose={() => undefined} /></AuthProvider>);
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Clientes")).not.toBeInTheDocument();
    expect(screen.queryByText("Usuários")).not.toBeInTheDocument();
    expect(screen.getByText("Documentos")).toBeInTheDocument();
  });

  it("exibe item de Usuários para quem tem a permissão users:read", async () => {
    vi.stubGlobal("fetch", authenticatedFetch(adminUser));
    render(<AuthProvider><Sidebar open onClose={() => undefined} /></AuthProvider>);
    expect(await screen.findByText("Usuários")).toBeInTheDocument();
  });

  it("exibe ForbiddenState em acesso direto sem permissão", async () => {
    vi.stubGlobal("fetch", authenticatedFetch(user));
    render(<AuthProvider><RequirePermission permission="clients:create"><div>Cadastro</div></RequirePermission></AuthProvider>);
    expect(await screen.findByText("Sem permissão para esta área")).toBeInTheDocument();
    expect(screen.queryByText("Cadastro")).not.toBeInTheDocument();
  });

  it("renderiza o estado de carregamento acessível", () => {
    render(<LoadingState title="Carregando dados" />);
    expect(screen.getByRole("status")).toHaveTextContent("Carregando dados");
  });

  it("renderiza erro amigável sem detalhes técnicos", () => {
    render(<ErrorState />);
    expect(screen.getByText("Não foi possível carregar os dados")).toBeInTheDocument();
    expect(screen.queryByText(/stack/i)).not.toBeInTheDocument();
  });

  it("o componente ForbiddenState comunica a autoridade do BFF", () => {
    render(<ForbiddenState />);
    expect(screen.getByText(/BFF continuará sendo a autoridade final/)).toBeInTheDocument();
  });
});

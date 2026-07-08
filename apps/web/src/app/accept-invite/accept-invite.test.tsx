import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AcceptInvitePage from "./page";
import { __testing } from "@/lib/api/http-client";
import { jsonResponse } from "@/test/fixtures";

const navigation = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  useSearchParams: () => new URLSearchParams(currentSearch),
}));

let currentSearch = "";

describe("Tela pública de aceitar convite", () => {
  beforeEach(() => {
    __testing.reset();
    navigation.replace.mockReset();
    currentSearch = "";
  });

  it("renderiza com token e mostra o formulário de senha", async () => {
    currentSearch = "token=abc123";
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(200, {
      email: "usuario@biason.net",
      name: "Nome do Usuário",
      status: "VALID",
      expiresAt: "2026-07-15T00:00:00Z",
    })));
    render(<AcceptInvitePage />);
    expect(await screen.findByText("Defina sua senha")).toBeInTheDocument();
    expect(screen.getByLabelText("Nova senha")).toBeInTheDocument();
  });

  it("mostra estado de convite inválido quando não há token", async () => {
    currentSearch = "";
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(404, {})));
    render(<AcceptInvitePage />);
    expect(await screen.findByText("Convite inválido")).toBeInTheDocument();
  });

  it("mostra ServiceUnavailableState quando o endpoint de convite não existe", async () => {
    currentSearch = "token=abc123";
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(404, { error: { code: "NOT_FOUND" } })));
    render(<AcceptInvitePage />);
    expect(await screen.findByText("Aceite de convite ainda não disponível")).toBeInTheDocument();
  });

  it("valida se a senha e a confirmação coincidem antes de enviar", async () => {
    currentSearch = "token=abc123";
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/auth/invitations/abc123") && !url.endsWith("/accept")) {
        return jsonResponse(200, { email: "usuario@biason.net", name: "Nome do Usuário", status: "VALID" });
      }
      return jsonResponse(200, { success: true });
    });
    vi.stubGlobal("fetch", fetchMock);
    const actor = userEvent.setup();
    render(<AcceptInvitePage />);
    await actor.type(await screen.findByLabelText("Nova senha"), "SenhaForte1");
    await actor.type(screen.getByLabelText("Confirmar senha"), "OutraSenha2");
    await actor.click(screen.getByRole("button", { name: /Ativar minha conta/i }));
    expect(await screen.findByText("As senhas informadas não coincidem.")).toBeInTheDocument();
  });
});

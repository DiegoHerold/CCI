import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import UsersPage from "./page";
import { AuthProvider } from "@/features/auth/auth-provider";
import { __testing } from "@/lib/api/http-client";
import { adminUser, jsonResponse, userRecord } from "@/test/fixtures";

function baseFetch(extra: (input: RequestInfo | URL, init?: RequestInit) => Response | Promise<Response> | undefined) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "token", tokenType: "Bearer", expiresIn: 900 });
    if (url.endsWith("/auth/me")) return jsonResponse(200, adminUser);
    if (url.includes("/clients?")) return jsonResponse(200, { items: [], page: 1, limit: 100, total: 0 });
    const result = extra(input, init);
    if (result) return result;
    return jsonResponse(404, { error: { code: "NOT_FOUND", message: "Rota não encontrada" } });
  });
}

describe("Tela de usuários", () => {
  beforeEach(() => __testing.reset());

  it("renderiza sem quebrar e lista usuários reais", async () => {
    const fetchMock = baseFetch((input) => {
      const url = String(input);
      if (url.includes("/users?")) return jsonResponse(200, { items: [userRecord], page: 1, limit: 50, total: 1 });
      return undefined;
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthProvider><UsersPage /></AuthProvider>);
    expect(await screen.findByText("Convidado Pendente")).toBeInTheDocument();
    expect(screen.getByText("convidado@biason.net")).toBeInTheDocument();
  });

  it("mostra ServiceUnavailableState quando GET /users não existe", async () => {
    const fetchMock = baseFetch(() => undefined);
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthProvider><UsersPage /></AuthProvider>);
    expect(await screen.findByText("Serviço ainda não disponível")).toBeInTheDocument();
  });

  it("formulário de convite valida nome e e-mail", async () => {
    const fetchMock = baseFetch((input) => {
      const url = String(input);
      if (url.includes("/users?")) return jsonResponse(200, { items: [], page: 1, limit: 50, total: 0 });
      return undefined;
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthProvider><UsersPage /></AuthProvider>);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo usuário/i }));
    await actor.click(screen.getByRole("button", { name: /Enviar convite/i }));
    expect(await screen.findByText("Informe o nome do usuário.")).toBeInTheDocument();
    expect(screen.getByText("Informe o e-mail do usuário.")).toBeInTheDocument();

    await actor.type(screen.getByLabelText(/Nome \*/), "Novo Usuário");
    await actor.type(screen.getByLabelText(/E-mail \*/), "email-invalido");
    await actor.click(screen.getByRole("button", { name: /Enviar convite/i }));
    expect(await screen.findByText("Informe um e-mail válido.")).toBeInTheDocument();
  });

  it("não finge envio de convite quando o endpoint não existe", async () => {
    const fetchMock = baseFetch((input) => {
      const url = String(input);
      if (url.includes("/users?")) return jsonResponse(200, { items: [], page: 1, limit: 50, total: 0 });
      return undefined;
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthProvider><UsersPage /></AuthProvider>);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo usuário/i }));
    await actor.type(screen.getByLabelText(/Nome \*/), "Novo Usuário");
    await actor.type(screen.getByLabelText(/E-mail \*/), "novo@biason.net");
    await actor.click(screen.getByRole("button", { name: /Enviar convite/i }));

    expect(await screen.findByText(/Convite ainda não disponível/)).toBeInTheDocument();
    expect(screen.queryByText(/Convite enviado/)).not.toBeInTheDocument();
  });

  it("só mostra sucesso de convite quando o BFF confirma", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "token", tokenType: "Bearer", expiresIn: 900 });
      if (url.endsWith("/auth/me")) return jsonResponse(200, adminUser);
      if (url.includes("/clients?")) return jsonResponse(200, { items: [], page: 1, limit: 100, total: 0 });
      if (url.includes("/users/invitations") && init?.method === "POST") {
        return jsonResponse(201, { id: "user-new", name: "Novo Usuário", email: "novo@biason.net", status: "PENDING_INVITE", roles: ["OPERATOR"] });
      }
      if (url.includes("/users?")) return jsonResponse(200, { items: [], page: 1, limit: 50, total: 0 });
      return jsonResponse(404, {});
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthProvider><UsersPage /></AuthProvider>);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo usuário/i }));
    await actor.type(screen.getByLabelText(/Nome \*/), "Novo Usuário");
    await actor.type(screen.getByLabelText(/E-mail \*/), "novo@biason.net");
    await actor.click(screen.getByRole("button", { name: /Enviar convite/i }));

    expect(await screen.findByText(/Convite enviado para/)).toBeInTheDocument();
    await waitFor(() => {
      const invitationCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes("/users/invitations"));
      expect(invitationCalls).toHaveLength(1);
    });
  });
});

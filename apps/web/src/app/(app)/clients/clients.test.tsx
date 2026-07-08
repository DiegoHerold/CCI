import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ClientsPage from "./page";
import { AuthProvider } from "@/features/auth/auth-provider";
import { __testing } from "@/lib/api/http-client";
import { adminUser, clientRecord, jsonResponse } from "@/test/fixtures";

function bootstrapFetch(handlers: Record<string, (init?: RequestInit) => Response | Promise<Response>>) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "token", tokenType: "Bearer", expiresIn: 900 });
    if (url.endsWith("/auth/me")) return jsonResponse(200, adminUser);
    for (const [suffix, handler] of Object.entries(handlers)) {
      if (url.includes(suffix)) return handler(init);
    }
    return jsonResponse(404, { error: { code: "NOT_FOUND", message: "Rota não encontrada" } });
  });
}

function renderClientsPage(fetchMock: ReturnType<typeof bootstrapFetch>) {
  vi.stubGlobal("fetch", fetchMock);
  return render(<AuthProvider><ClientsPage /></AuthProvider>);
}

describe("Tela de clientes", () => {
  beforeEach(() => __testing.reset());

  it("renderiza sem quebrar e lista clientes reais", async () => {
    const fetchMock = bootstrapFetch({
      "/clients?": () => jsonResponse(200, { items: [clientRecord], page: 1, limit: 50, total: 1 }),
    });
    renderClientsPage(fetchMock);
    expect(await screen.findByText("Aurora")).toBeInTheDocument();
    expect(screen.getByText("Clientes")).toBeInTheDocument();
  });

  it("mostra ServiceUnavailableState quando GET /clients não existe", async () => {
    const fetchMock = bootstrapFetch({});
    renderClientsPage(fetchMock);
    expect(await screen.findByText("Serviço ainda não disponível")).toBeInTheDocument();
  });

  it("formulário de criação valida campos obrigatórios e CNPJ", async () => {
    const fetchMock = bootstrapFetch({
      "/clients?": () => jsonResponse(200, { items: [], page: 1, limit: 50, total: 0 }),
    });
    renderClientsPage(fetchMock);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo cliente/i }));

    await actor.click(screen.getByRole("button", { name: /Cadastrar cliente/i }));
    expect(await screen.findByText("Informe a razão social.")).toBeInTheDocument();
    expect(screen.getByText("Informe o CNPJ.")).toBeInTheDocument();

    await actor.type(screen.getByLabelText(/Razão social/), "Empresa Exemplo LTDA");
    await actor.type(screen.getByLabelText(/^CNPJ/), "11.222.333/0001-99");
    await actor.click(screen.getByRole("button", { name: /Cadastrar cliente/i }));
    expect(await screen.findByText(/CNPJ inválido/)).toBeInTheDocument();

    const postCalls = fetchMock.mock.calls.filter(([url, init]) => String(url).includes("/clients") && (init as RequestInit | undefined)?.method === "POST");
    expect(postCalls).toHaveLength(0);
  });

  it("só mostra sucesso quando o BFF confirma a criação e recarrega a lista", async () => {
    let listCalls = 0;
    const fetchMock = bootstrapFetch({
      "/clients?": () => {
        listCalls += 1;
        return jsonResponse(200, { items: listCalls > 1 ? [clientRecord] : [], page: 1, limit: 50, total: listCalls > 1 ? 1 : 0 });
      },
    });
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "token", tokenType: "Bearer", expiresIn: 900 });
      if (url.endsWith("/auth/me")) return jsonResponse(200, adminUser);
      if (url.includes("/clients") && init?.method === "POST") return jsonResponse(201, clientRecord);
      if (url.includes("/clients?")) {
        listCalls += 1;
        return jsonResponse(200, { items: listCalls > 1 ? [clientRecord] : [], page: 1, limit: 50, total: listCalls > 1 ? 1 : 0 });
      }
      return jsonResponse(404, {});
    });

    render(<AuthProvider><ClientsPage /></AuthProvider>);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo cliente/i }));
    await actor.type(screen.getByLabelText(/Razão social/), "Empresa Exemplo LTDA");
    await actor.type(screen.getByLabelText(/^CNPJ/), "11.222.333/0001-81");
    await actor.click(screen.getByRole("button", { name: /Cadastrar cliente/i }));

    expect(await screen.findByText(/cadastrado com sucesso/)).toBeInTheDocument();
    await waitFor(() => expect(listCalls).toBeGreaterThan(1));
  });

  it("não cria cliente fake quando o endpoint de criação não existe", async () => {
    const fetchMock = bootstrapFetch({
      "/clients?": () => jsonResponse(200, { items: [], page: 1, limit: 50, total: 0 }),
    });
    renderClientsPage(fetchMock);
    const actor = userEvent.setup();
    await actor.click(await screen.findByRole("button", { name: /Novo cliente/i }));
    await actor.type(screen.getByLabelText(/Razão social/), "Empresa Exemplo LTDA");
    await actor.type(screen.getByLabelText(/^CNPJ/), "11.222.333/0001-81");
    await actor.click(screen.getByRole("button", { name: /Cadastrar cliente/i }));

    expect(await screen.findByText(/Cadastro ainda não concluído/)).toBeInTheDocument();
    expect(screen.queryByText(/cadastrado com sucesso/)).not.toBeInTheDocument();
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("button", { name: /Cadastrar cliente/i })).toBeInTheDocument();
  });
});

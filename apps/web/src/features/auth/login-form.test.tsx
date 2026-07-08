import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "./auth-provider";
import { LoginForm } from "./login-form";
import { __testing } from "@/lib/api/http-client";
import { jsonResponse, user } from "@/test/fixtures";

const navigation = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/login",
}));

describe("LoginForm", () => {
  beforeEach(() => {
    __testing.reset();
    navigation.replace.mockReset();
  });

  it("renderiza os campos e a ação de entrada", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(401, { error: { code: "HTTP_ERROR" } })));
    render(<AuthProvider><LoginForm /></AuthProvider>);
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByLabelText("Senha")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Entrar no cockpit/i })).toBeEnabled();
  });

  it("envia credenciais ao BFF e valida o usuário em /auth/me", async () => {
    const fetchMock = vi.fn(async (...args: [RequestInfo | URL, RequestInit?]) => {
      const input = args[0];
      const url = String(input);
      if (url.endsWith("/auth/refresh")) return jsonResponse(401, {});
      if (url.endsWith("/auth/login")) return jsonResponse(200, { accessToken: "token", tokenType: "Bearer", expiresIn: 900, user });
      if (url.endsWith("/auth/me")) return jsonResponse(200, user);
      return jsonResponse(404, {});
    });
    vi.stubGlobal("fetch", fetchMock);
    const actor = userEvent.setup();
    render(<AuthProvider><LoginForm /></AuthProvider>);
    await actor.type(screen.getByLabelText("E-mail"), "marina@contabilidade.com.br");
    await actor.type(screen.getByLabelText("Senha"), "Senha123");
    await actor.click(await screen.findByRole("button", { name: /Entrar no cockpit/i }));

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/dashboard"));
    const loginCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/auth/login"));
    expect(loginCall).toBeDefined();
    expect(JSON.parse(String((loginCall?.[1] as RequestInit).body))).toEqual({ email: user.email, password: "Senha123" });
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/auth/me"))).toBe(true);
  });

  it("exibe mensagem segura para credenciais inválidas", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/auth/login")) return jsonResponse(401, { error: { code: "INVALID_CREDENTIALS" } });
      return jsonResponse(401, {});
    }));
    const actor = userEvent.setup();
    render(<AuthProvider><LoginForm /></AuthProvider>);
    await actor.type(screen.getByLabelText("E-mail"), "pessoa@empresa.com");
    await actor.type(screen.getByLabelText("Senha"), "incorreta");
    await actor.click(await screen.findByRole("button", { name: /Entrar no cockpit/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou senha inválidos");
  });
});

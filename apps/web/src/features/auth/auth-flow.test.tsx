import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./auth-provider";
import { RequireAuth } from "./require-auth";
import { __testing } from "@/lib/api/http-client";
import { authenticatedFetch, jsonResponse } from "@/test/fixtures";

const navigation = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: navigation.replace }),
  usePathname: () => "/dashboard",
}));

function SessionHarness() {
  const { status, logout } = useAuth();
  return <><span>{status}</span><button onClick={() => void logout()}>Sair</button></>;
}

describe("sessão autenticada", () => {
  beforeEach(() => { __testing.reset(); navigation.replace.mockReset(); });

  it("libera o dashboard após refresh e /auth/me", async () => {
    vi.stubGlobal("fetch", authenticatedFetch());
    render(<AuthProvider><RequireAuth><div>Dashboard protegido</div></RequireAuth></AuthProvider>);
    expect(await screen.findByText("Dashboard protegido")).toBeInTheDocument();
  });

  it("redireciona usuário sem sessão para o login", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(401, {})));
    render(<AuthProvider><RequireAuth><div>Segredo</div></RequireAuth></AuthProvider>);
    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("Segredo")).not.toBeInTheDocument();
  });

  it("redireciona quando /auth/me falha mesmo após refresh", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => String(input).endsWith("/auth/refresh") ? jsonResponse(200, { accessToken: "token" }) : jsonResponse(401, {})));
    render(<AuthProvider><RequireAuth><div>Segredo</div></RequireAuth></AuthProvider>);
    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/login"));
  });

  it("logout chama o BFF e limpa a sessão local", async () => {
    const fetchMock = authenticatedFetch();
    vi.stubGlobal("fetch", fetchMock);
    const actor = userEvent.setup();
    render(<AuthProvider><SessionHarness /></AuthProvider>);
    expect(await screen.findByText("authenticated")).toBeInTheDocument();
    await actor.click(screen.getByRole("button", { name: "Sair" }));
    expect(await screen.findByText("unauthenticated")).toBeInTheDocument();
    const calls = fetchMock.mock.calls as unknown as Array<[RequestInfo | URL, RequestInit?]>;
    expect(calls.some((call) => String(call[0]).endsWith("/auth/logout"))).toBe(true);
  });
});

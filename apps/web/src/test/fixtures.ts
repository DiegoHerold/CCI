import type { AuthUser, ClientContextResponse, ClientRecord, UserRecord } from "@/types/api";
import { vi } from "vitest";

export const user: AuthUser = {
  id: "user-1",
  name: "Marina Costa",
  email: "marina@contabilidade.com.br",
  status: "ACTIVE",
  roles: ["VIEWER"],
  permissions: ["conferences:read"],
};

export const adminUser: AuthUser = {
  id: "user-admin",
  name: "Administradora CCI",
  email: "admin@biason.net",
  status: "ACTIVE",
  roles: ["ADMIN"],
  permissions: [
    "users:read",
    "users:create",
    "users:update",
    "users:disable",
    "clients:read",
    "clients:create",
  ],
};

export const clientRecord: ClientRecord = {
  id: "client-1",
  code: "0001",
  name: "Organização Contábil Aurora LTDA",
  tradeName: "Aurora",
  cnpj: "11.222.333/0001-81",
  status: "ACTIVE",
  city: "Gravataí",
  state: "RS",
};

export const userRecord: UserRecord = {
  id: "user-2",
  name: "Convidado Pendente",
  email: "convidado@biason.net",
  status: "PENDING_INVITE",
  roles: ["OPERATOR"],
  inviteSentAt: "2026-07-01T10:00:00Z",
  inviteAcceptedAt: null,
};

export const contextWithoutClients: ClientContextResponse = {
  user,
  clients: [],
  defaultClientId: null,
  currentCompetence: { period: "2026-07", year: 2026, month: 7 },
};

export const contextWithClient: ClientContextResponse = {
  user,
  clients: [{
    id: "client-1",
    code: null,
    name: "Organização Contábil Aurora",
    tradeName: "Aurora",
    cnpj: "11.222.333/0001-81",
    status: "ACTIVE",
    userClientRole: "CLIENT_VIEWER",
    responsibilityArea: "ACCOUNTING",
    isPrimaryResponsible: false,
  }],
  defaultClientId: "client-1",
  currentCompetence: { period: "2026-07", year: 2026, month: 7 },
};

export function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function authenticatedFetch(currentUser: AuthUser = user, context = contextWithoutClients) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "renewed", tokenType: "Bearer", expiresIn: 900 });
    if (url.endsWith("/auth/me")) return jsonResponse(200, currentUser);
    if (url.endsWith("/client-context")) return jsonResponse(200, context);
    if (url.endsWith("/auth/logout") && init?.method === "POST") return jsonResponse(200, { success: true });
    return jsonResponse(404, { error: { code: "NOT_FOUND", message: "Not found" } });
  });
}

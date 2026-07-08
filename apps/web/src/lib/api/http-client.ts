import type { BffErrorPayload, TokenResponse } from "@/types/api";

const DEFAULT_BFF_URL = "http://localhost:8000/api/v1";

export const BFF_URL = (process.env.NEXT_PUBLIC_BFF_URL || DEFAULT_BFF_URL).replace(/\/$/, "");

let accessToken: string | null = null;
let refreshRequest: Promise<string> | null = null;
let sessionExpiredHandler: (() => void) | null = null;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly correlationId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function hasAccessToken() {
  return Boolean(accessToken);
}

export function setSessionExpiredHandler(handler: (() => void) | null) {
  sessionExpiredHandler = handler;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json().catch(() => ({}))) as T & BffErrorPayload;
  if (response.ok) return payload;

  throw new ApiError(
    response.status,
    payload.error?.code || "HTTP_ERROR",
    payload.error?.message || payload.detail || "Não foi possível concluir a solicitação.",
    payload.error?.correlation_id,
  );
}

async function rawRequest<T>(path: string, init: RequestInit = {}, token?: string | null) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${BFF_URL}${path}`, {
      ...init,
      headers,
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Não foi possível conectar ao BFF.");
  }
  return parseResponse<T>(response);
}

export async function refreshAccessToken(): Promise<string> {
  if (!refreshRequest) {
    refreshRequest = rawRequest<TokenResponse>("/auth/refresh", { method: "POST" })
      .then((response) => {
        setAccessToken(response.accessToken);
        return response.accessToken;
      })
      .finally(() => {
        refreshRequest = null;
      });
  }
  return refreshRequest;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: { authenticated?: boolean; retryOnUnauthorized?: boolean } = {},
): Promise<T> {
  const authenticated = options.authenticated ?? true;
  try {
    return await rawRequest<T>(path, init, authenticated ? accessToken : null);
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      authenticated &&
      options.retryOnUnauthorized !== false
    ) {
      try {
        const renewedToken = await refreshAccessToken();
        return await rawRequest<T>(path, init, renewedToken);
      } catch (refreshError) {
        setAccessToken(null);
        sessionExpiredHandler?.();
        throw refreshError;
      }
    }
    throw error;
  }
}

export const __testing = {
  reset() {
    accessToken = null;
    refreshRequest = null;
    sessionExpiredHandler = null;
  },
};

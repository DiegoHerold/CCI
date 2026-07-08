import { ApiError } from "./http-client";
import type { ApiErrorCode } from "@/types/api";

const NOT_IMPLEMENTED_HINTS = [
  "not implemented",
  "não implementad",
  "not found",
  "rota não encontrada",
  "endpoint não",
];

/**
 * Classifica qualquer erro de chamada ao BFF em um código estável, usado por
 * todas as telas administrativas para decidir qual estado visual exibir.
 * Endpoint ausente (404) ou não pronto (501/503) sempre vira
 * SERVICE_UNAVAILABLE, nunca um erro bruto.
 */
export function classifyApiError(error: unknown): ApiErrorCode {
  if (!(error instanceof ApiError)) return "NETWORK_ERROR";

  if (error.status === 0) return "NETWORK_ERROR";
  if (error.status === 401) return "UNAUTHORIZED";
  if (error.status === 403) return "FORBIDDEN";
  if (error.status === 404) return "SERVICE_UNAVAILABLE";
  if (error.status === 422 || error.status === 400) return "VALIDATION_ERROR";
  if (error.status === 501 || error.status === 503) return "SERVICE_UNAVAILABLE";

  const messageHints = `${error.code} ${error.message}`.toLowerCase();
  if (NOT_IMPLEMENTED_HINTS.some((hint) => messageHints.includes(hint))) {
    return "SERVICE_UNAVAILABLE";
  }

  return "UNKNOWN_ERROR";
}

export function isEndpointUnavailable(error: unknown): boolean {
  const code = classifyApiError(error);
  return code === "SERVICE_UNAVAILABLE" || code === "NETWORK_ERROR";
}

/** Mensagem segura para exibir em formulários quando o BFF rejeita a operação. */
export function friendlyErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    const code = classifyApiError(error);
    if (code === "VALIDATION_ERROR") return error.message || fallback;
    if (code === "UNAUTHORIZED") return "Sua sessão expirou. Faça login novamente.";
    if (code === "FORBIDDEN") return "Você não tem permissão para executar esta ação.";
  }
  return fallback;
}

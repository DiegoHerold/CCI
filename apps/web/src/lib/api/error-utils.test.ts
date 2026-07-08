import { describe, expect, it } from "vitest";
import { classifyApiError, isEndpointUnavailable } from "./error-utils";
import { ApiError } from "./http-client";

describe("classificação de erros do BFF", () => {
  it("mapeia 404 para SERVICE_UNAVAILABLE (endpoint ainda não implementado)", () => {
    const error = new ApiError(404, "NOT_FOUND", "Rota não encontrada");
    expect(classifyApiError(error)).toBe("SERVICE_UNAVAILABLE");
    expect(isEndpointUnavailable(error)).toBe(true);
  });

  it("mapeia 501 e 503 para SERVICE_UNAVAILABLE", () => {
    expect(classifyApiError(new ApiError(501, "NOT_IMPLEMENTED", "Ainda não implementado"))).toBe("SERVICE_UNAVAILABLE");
    expect(classifyApiError(new ApiError(503, "UNAVAILABLE", "Serviço indisponível"))).toBe("SERVICE_UNAVAILABLE");
  });

  it("mapeia 401 para UNAUTHORIZED e 403 para FORBIDDEN", () => {
    expect(classifyApiError(new ApiError(401, "UNAUTHORIZED", "Sem sessão"))).toBe("UNAUTHORIZED");
    expect(classifyApiError(new ApiError(403, "FORBIDDEN", "Sem permissão"))).toBe("FORBIDDEN");
  });

  it("mapeia 422 para VALIDATION_ERROR", () => {
    expect(classifyApiError(new ApiError(422, "VALIDATION_ERROR", "CNPJ inválido"))).toBe("VALIDATION_ERROR");
  });

  it("mapeia falha de rede (status 0) para NETWORK_ERROR", () => {
    const error = new ApiError(0, "NETWORK_ERROR", "Não foi possível conectar ao BFF.");
    expect(classifyApiError(error)).toBe("NETWORK_ERROR");
    expect(isEndpointUnavailable(error)).toBe(true);
  });

  it("erros desconhecidos não são tratados como indisponibilidade", () => {
    const error = new ApiError(500, "INTERNAL_ERROR", "Erro interno");
    expect(classifyApiError(error)).toBe("UNKNOWN_ERROR");
    expect(isEndpointUnavailable(error)).toBe(false);
  });
});

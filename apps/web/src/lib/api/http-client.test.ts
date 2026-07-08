import { readFileSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BFF_URL, __testing, apiRequest, setAccessToken } from "./http-client";
import { jsonResponse } from "@/test/fixtures";

describe("HTTP client do BFF", () => {
  beforeEach(() => __testing.reset());

  it("usa somente a URL pública do BFF", () => {
    expect(BFF_URL).toContain("8000/api/v1");
    expect(BFF_URL).not.toMatch(/identity-service|client-service|postgres/i);
  });

  it("envia credentials include e o Bearer mantido em memória", async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    setAccessToken("access-only-in-memory");
    await apiRequest("/auth/me", {}, { retryOnUnauthorized: false });
    const calls = fetchMock.mock.calls as unknown as Array<[RequestInfo | URL, RequestInit]>;
    const init = calls[0][1];
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer access-only-in-memory");
  });

  it("renova uma vez após 401 e repete a chamada original", async () => {
    let protectedCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/auth/refresh")) return jsonResponse(200, { accessToken: "renewed" });
      protectedCalls += 1;
      return protectedCalls === 1 ? jsonResponse(401, {}) : jsonResponse(200, { ok: true });
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiRequest<{ ok: boolean }>("/client-context")).resolves.toEqual({ ok: true });
    expect(protectedCalls).toBe(2);
  });

  it("não contém clientes mockados no código de produção", () => {
    const sourceRoot = join(process.cwd(), "src");
    const productionFiles = [
      "app/(app)/dashboard/page.tsx",
      "features/context/operational-context-provider.tsx",
      "lib/api/client-context-api.ts",
    ];
    for (const file of productionFiles) {
      const source = readFileSync(join(sourceRoot, file), "utf8");
      expect(source).not.toMatch(/Empresa Exemplo|Cliente Teste|CNPJ fake/i);
    }
  });
});

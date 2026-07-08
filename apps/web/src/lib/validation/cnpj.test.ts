import { describe, expect, it } from "vitest";
import { formatCnpj, isValidCnpj } from "./cnpj";

describe("validação de CNPJ", () => {
  it("aceita um CNPJ válido com máscara", () => {
    expect(isValidCnpj("11.222.333/0001-81")).toBe(true);
  });

  it("aceita um CNPJ válido sem máscara", () => {
    expect(isValidCnpj("11222333000181")).toBe(true);
  });

  it("rejeita CNPJ com dígito verificador incorreto", () => {
    expect(isValidCnpj("11.222.333/0001-99")).toBe(false);
  });

  it("rejeita sequência repetida", () => {
    expect(isValidCnpj("11111111111111")).toBe(false);
  });

  it("rejeita quantidade de dígitos incorreta", () => {
    expect(isValidCnpj("123")).toBe(false);
  });

  it("formata progressivamente enquanto o usuário digita", () => {
    expect(formatCnpj("11222333000181")).toBe("11.222.333/0001-81");
    expect(formatCnpj("1122")).toBe("11.22");
  });
});

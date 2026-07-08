/**
 * Validação básica de CNPJ no frontend. Serve apenas para dar feedback rápido
 * ao usuário; a validação de negócio (duplicidade, formato oficial) continua
 * sendo responsabilidade do Client Service, exposta pelo BFF.
 */
export function normalizeCnpjDigits(value: string): string {
  return value.replace(/\D/g, "");
}

export function formatCnpj(value: string): string {
  const digits = normalizeCnpjDigits(value).slice(0, 14);
  const parts = [
    digits.slice(0, 2),
    digits.slice(2, 5),
    digits.slice(5, 8),
    digits.slice(8, 12),
    digits.slice(12, 14),
  ];
  let formatted = parts[0];
  if (parts[1]) formatted += `.${parts[1]}`;
  if (parts[2]) formatted += `.${parts[2]}`;
  if (parts[3]) formatted += `/${parts[3]}`;
  if (parts[4]) formatted += `-${parts[4]}`;
  return formatted;
}

function calculateCheckDigit(digits: string, weights: number[]): number {
  const sum = weights.reduce((total, weight, index) => total + weight * Number(digits[index]), 0);
  const remainder = sum % 11;
  return remainder < 2 ? 0 : 11 - remainder;
}

export function isValidCnpj(value: string): boolean {
  const digits = normalizeCnpjDigits(value);
  if (digits.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(digits)) return false;

  const firstWeights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const secondWeights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

  const firstDigit = calculateCheckDigit(digits, firstWeights);
  if (firstDigit !== Number(digits[12])) return false;

  const secondDigit = calculateCheckDigit(digits, secondWeights);
  if (secondDigit !== Number(digits[13])) return false;

  return true;
}

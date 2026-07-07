export type RuleResultStatus = "approved" | "divergent" | "error" | "pending" | "not_applicable" | "needs_review";
export interface RuleEvaluationResult { status: RuleResultStatus; operator: string; left_value?: unknown; right_value?: unknown; difference?: number | null; message: string; details: RuleEvaluationResult[] }

// A implementação executável inicial está em Python. A versão TypeScript será
// adicionada somente quando houver um consumidor real que justifique mantê-la.

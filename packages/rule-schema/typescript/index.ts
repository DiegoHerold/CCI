export type RuleStatus = "draft" | "active" | "inactive" | "archived";
export type RuleOperator = "equals" | "not_equals" | "greater_than" | "less_than" | "greater_or_equal" | "less_or_equal" | "exists" | "not_exists" | "difference_less_than" | "sum_equals" | "formula" | "and" | "or" | "if_then";
export type RuleOperand = string | number | boolean | null;
export interface RuleLogic { operator: RuleOperator; left?: RuleOperand; right?: RuleOperand; items?: string[]; conditions?: RuleLogic[]; tolerance?: number }
export interface Rule { rule_id: string; client_id: string; model_id: string; name: string; description: string; version: number; status: RuleStatus; logic: RuleLogic; required_variables: string[]; tolerance?: number | null; created_by?: string | null; created_at?: string | null; updated_at?: string | null; activated_at?: string | null }

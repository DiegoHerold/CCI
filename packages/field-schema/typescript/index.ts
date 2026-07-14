export type FieldType = "string" | "integer" | "decimal" | "money" | "boolean" | "date" | "datetime" | "object" | "array" | "table" | "calculated";
export interface FieldDefinition { field_id: string; path: string; label: string; field_type: FieldType; required: boolean; children?: FieldDefinition[]; formula?: string | null }

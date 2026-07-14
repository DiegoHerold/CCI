export type FieldType =
  | "text"
  | "number"
  | "money"
  | "date"
  | "month"
  | "cnpj"
  | "cpf"
  | "boolean"
  | "percentage"
  | "account_code"
  | "object"
  | "array"
  | "table"
  | "calculated"
  | "unknown";

export interface FieldDefinition {
  id: string;
  template_id: string;
  parent_field_id?: string | null;
  field_path: string;
  label: string;
  description?: string | null;
  field_type: FieldType;
  is_required: boolean;
  important: boolean;
  is_repeated: boolean;
  is_object: boolean;
  is_array: boolean;
  order_index: number;
}

export interface ObjectField extends FieldDefinition {
  field_type: "object";
  is_object: true;
}

export interface ArrayField extends FieldDefinition {
  field_type: "array";
  is_repeated: true;
  is_array: true;
}

export interface TableField extends FieldDefinition {
  field_type: "table";
  is_repeated: true;
}

export interface CalculatedField extends FieldDefinition {
  field_type: "calculated";
  formula?: string | null;
}

export interface FieldCard {
  field_id: string;
  field_path: string;
  label: string;
  field_type: FieldType;
  template_id: string;
  is_repeated: boolean;
  evidence_required: boolean;
  important: boolean;
}

export interface FieldTreeNode {
  key: string;
  label: string;
  path: string;
  field?: FieldDefinition | null;
  children: FieldTreeNode[];
}

export interface CreateFieldRequest {
  parent_field_id?: string | null;
  field_path: string;
  label: string;
  description?: string | null;
  field_type: FieldType;
  is_required: boolean;
  important: boolean;
  is_repeated: boolean;
  is_object: boolean;
  is_array: boolean;
  order_index: number;
}

export interface UpdateFieldRequest {
  parent_field_id?: string | null;
  label?: string | null;
  description?: string | null;
  field_type?: FieldType | null;
  is_required?: boolean | null;
  important?: boolean | null;
  is_repeated?: boolean | null;
  is_object?: boolean | null;
  is_array?: boolean | null;
  order_index?: number | null;
}

export type FieldMappingStatus = "unmapped" | "mapped" | "partial";

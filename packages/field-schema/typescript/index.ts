export type FieldType =
  | "text"
  | "number"
  | "money"
  | "date"
  | "month"
  | "cnpj"
  | "cpf"
  | "boolean"
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
}

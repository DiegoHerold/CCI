import type { FieldTreeNode, TemplateField } from "../types/templateBuilder";

function displayPart(part: string) {
  return part.replace("[]", "[]");
}

export function buildFieldTree(fields: TemplateField[]): FieldTreeNode[] {
  const root: FieldTreeNode[] = [];
  const byPath = new Map<string, FieldTreeNode>();

  for (const field of [...fields].sort((a, b) => a.fieldPath.localeCompare(b.fieldPath))) {
    const parts = field.fieldPath.split(".");
    let prefix = "";
    let level = root;
    parts.forEach((part, index) => {
      prefix = prefix ? `${prefix}.${part}` : part;
      let node = byPath.get(prefix);
      if (!node) {
        node = { key: prefix, label: displayPart(part), path: prefix, children: [] };
        byPath.set(prefix, node);
        level.push(node);
      }
      if (index === parts.length - 1) node.field = field;
      level = node.children;
    });
  }

  return root;
}

export function defaultLabelFromPath(path: string) {
  const last = path.split(".").at(-1) || path;
  return last.replace("[]", "").replaceAll("_", " ");
}

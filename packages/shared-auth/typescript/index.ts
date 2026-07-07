export type Role = "admin" | "coordinator" | "analyst" | "reviewer" | "read_only";

export interface UserClaims {
  sub: string;
  email: string;
  name: string;
  roles: Role[];
  permissions: string[];
  client_ids: string[];
  iat: number;
  exp: number;
}

export const ROLE_PERMISSIONS: Record<Role, readonly string[]> = {
  admin: ["*"],
  coordinator: ["users.read", "users.update", "clients.create", "clients.read", "clients.update", "clients.assign_user", "models.create", "models.read", "models.update", "models.version", "models.activate", "documents.import", "documents.read", "documents.confirm", "documents.reject", "variables.read", "variables.confirm", "variables.correct", "variables.ignore", "rules.create", "rules.read", "rules.update", "rules.version", "rules.activate", "rules.disable", "executions.start", "executions.read", "executions.cancel", "executions.reprocess", "results.read", "audit.read", "reports.generate", "reports.read", "reports.download", "logs.read"],
  analyst: ["clients.read", "clients.update", "models.read", "documents.import", "documents.read", "documents.confirm", "documents.reject", "variables.read", "variables.confirm", "variables.correct", "variables.ignore", "rules.create", "rules.read", "rules.update", "rules.version", "executions.start", "executions.read", "executions.reprocess", "results.read", "audit.read", "reports.generate", "reports.read", "reports.download", "logs.read"],
  reviewer: ["clients.read", "models.read", "documents.read", "documents.confirm", "documents.reject", "variables.read", "variables.confirm", "variables.correct", "variables.ignore", "rules.read", "executions.read", "results.read", "audit.read", "reports.generate", "reports.read", "reports.download", "logs.read"],
  read_only: ["users.read", "clients.read", "models.read", "documents.read", "variables.read", "rules.read", "executions.read", "results.read", "audit.read", "reports.read", "reports.download", "logs.read"],
};

export function hasRole(claims: UserClaims, role: Role): boolean {
  return claims.roles.includes(role);
}

export function hasPermission(claims: UserClaims, permission: string): boolean {
  if (claims.roles.includes("admin") || claims.permissions.includes(permission)) return true;
  return claims.roles.some((role) => ROLE_PERMISSIONS[role].includes(permission));
}

export function canAccessClient(claims: UserClaims, clientId: string): boolean {
  return claims.roles.includes("admin") || claims.client_ids.includes(clientId);
}

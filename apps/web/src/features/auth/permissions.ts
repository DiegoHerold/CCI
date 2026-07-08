import type { AuthUser } from "@/types/api";

export function hasPermission(user: AuthUser | null, permission?: string) {
  if (!permission) return true;
  if (!user) return false;
  return user.roles.includes("ADMIN") || user.permissions.includes(permission);
}

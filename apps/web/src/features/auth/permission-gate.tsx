"use client";

import { useAuth } from "./auth-provider";
import { hasPermission } from "./permissions";

export function PermissionGate({
  permission,
  children,
  fallback = null,
}: {
  permission?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { user } = useAuth();
  return hasPermission(user, permission) ? children : fallback;
}

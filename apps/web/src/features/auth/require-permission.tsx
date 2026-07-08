"use client";

import { ForbiddenState } from "@/components/states/forbidden-state";
import { useAuth } from "./auth-provider";
import { hasPermission } from "./permissions";

export function RequirePermission({ permission, children }: { permission: string; children: React.ReactNode }) {
  const { user } = useAuth();
  return hasPermission(user, permission) ? children : <ForbiddenState />;
}

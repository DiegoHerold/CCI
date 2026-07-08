"use client";

import type { LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/states/empty-state";
import { RequirePermission } from "@/features/auth/require-permission";

export function ModulePlaceholder({ title, description, emptyTitle, emptyDescription, icon, permission }: { title: string; description: string; emptyTitle: string; emptyDescription: string; icon: LucideIcon; permission?: string }) {
  const content = <div className="space-y-7"><PageHeader eyebrow="Módulo preparado" title={title} description={description} /><EmptyState icon={icon} title={emptyTitle} description={emptyDescription} /></div>;
  return permission ? <RequirePermission permission={permission}>{content}</RequirePermission> : content;
}

import { RequirePermission } from "@/features/auth/require-permission";
import { TemplateBuilderPage } from "@/features/template-builder/components/TemplateBuilderPage";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ templateId: string }>;
  searchParams: Promise<{ documentId?: string }>;
}) {
  const { templateId } = await params;
  const { documentId } = await searchParams;
  return (
    <RequirePermission permission="conferences:read">
      <TemplateBuilderPage templateId={templateId} documentId={documentId} />
    </RequirePermission>
  );
}

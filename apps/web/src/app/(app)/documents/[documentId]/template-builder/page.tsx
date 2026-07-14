import { RequirePermission } from "@/features/auth/require-permission";
import { GuidedTemplateBuilderFromDocument } from "@/features/template-builder/components/GuidedTemplateBuilderFromDocument";

export default async function Page({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return (
    <RequirePermission permission="conferences:read">
      <GuidedTemplateBuilderFromDocument documentId={documentId} />
    </RequirePermission>
  );
}

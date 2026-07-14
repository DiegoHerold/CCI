import { DocumentViewerPage } from "@/features/document-viewer/components/DocumentViewerPage";
import { RequirePermission } from "@/features/auth/require-permission";

export default async function Page({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return (
    <RequirePermission permission="conferences:read">
      <DocumentViewerPage documentId={documentId} />
    </RequirePermission>
  );
}

import { RequirePermission } from "@/features/auth/require-permission";
import { ExtractionReviewPage } from "@/features/extraction-review/components/ExtractionReviewPage";

export default async function Page({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return (
    <RequirePermission permission="conferences:read">
      <ExtractionReviewPage documentId={documentId} />
    </RequirePermission>
  );
}

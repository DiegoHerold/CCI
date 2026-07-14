import { apiRequest } from "@/lib/api/http-client";
import type {
  DocumentPreviewApiResponse,
  DocumentPreviewStatusResponse,
  DocumentRecord,
  DocumentsListResponse,
  PreviewRequestResponse,
} from "../types/preview";

export const documentPreviewApi = {
  list(params: { page?: number; limit?: number; clientId?: string; competenceId?: string } = {}) {
    const query = new URLSearchParams();
    query.set("page", String(params.page ?? 1));
    query.set("limit", String(params.limit ?? 20));
    if (params.clientId) query.set("client_id", params.clientId);
    if (params.competenceId) query.set("competence_id", params.competenceId);
    return apiRequest<DocumentsListResponse>(`/documents?${query.toString()}`);
  },

  getDocument(documentId: string) {
    return apiRequest<DocumentRecord>(`/documents/${documentId}`);
  },

  getPreviewStatus(documentId: string) {
    return apiRequest<DocumentPreviewStatusResponse>(`/documents/${documentId}/preview/status`);
  },

  getPreview(documentId: string) {
    return apiRequest<DocumentPreviewApiResponse>(`/documents/${documentId}/preview`);
  },

  requestPreview(documentId: string) {
    return apiRequest<PreviewRequestResponse>(`/documents/${documentId}/preview`, { method: "POST" });
  },

  reprocessPreview(documentId: string) {
    return apiRequest<PreviewRequestResponse>(`/documents/${documentId}/preview/reprocess`, { method: "POST" });
  },
};

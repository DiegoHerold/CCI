import { apiRequest } from "@/lib/api/http-client";

export interface DocumentFlowState {
  document: {
    documentId?: string;
    document_id?: string;
    filename?: string | null;
    status?: string | null;
    file_format?: string | null;
    client_id?: string | null;
    competence_id?: string | null;
  };
  preview: {
    status: string;
    requires_ocr: boolean;
  };
  template_matching: {
    status: string;
    confidence?: number | null;
    best_candidate?: Record<string, unknown> | null;
    candidates: Record<string, unknown>[];
    matching_run_id?: string | null;
    manual_override?: boolean;
  };
  template: {
    template_id?: string | null;
    template_version_id?: string | null;
    status?: string | null;
  };
  extraction: {
    job_id?: string | null;
    status: string;
    error_message?: string | null;
  };
  normalization: {
    status: string;
  };
  result: {
    result_id?: string | null;
    status?: string | null;
    field_count: number;
    normalized_count: number;
    requires_review_count: number;
  };
  next_action: {
    type: string;
    label: string;
  };
}

export const documentFlowApi = {
  getFlowState(documentId: string) {
    return apiRequest<DocumentFlowState>(`/documents/${documentId}/flow-state`);
  },

  runTemplateMatch(documentId: string) {
    return apiRequest(`/documents/${documentId}/template-match`, { method: "POST", body: JSON.stringify({ forceReprocess: true }) });
  },

  confirmTemplate(documentId: string, templateId: string, templateVersionId: string, reason = "Confirmado no fluxo guiado") {
    return apiRequest(`/documents/${documentId}/template-match/confirm`, {
      method: "POST",
      body: JSON.stringify({ templateId, templateVersionId, reason }),
    });
  },

  startExtraction(documentId: string) {
    return apiRequest(`/documents/${documentId}/extract`, { method: "POST", body: JSON.stringify({ forceReprocess: true }) });
  },
};

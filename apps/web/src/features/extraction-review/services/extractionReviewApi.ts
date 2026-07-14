import { apiRequest } from "@/lib/api/http-client";

export interface ExtractionResultSummary {
  extractionResultId: string;
  extractionJobId: string;
  documentId: string;
  templateId: string;
  templateVersionId: string;
  status: string;
  fieldCount: number;
  normalizedCount: number;
  requiresReviewCount: number;
  errorCount: number;
  warningCount: number;
}

export interface ExtractedFieldValue {
  fieldValueId: string;
  extractionResultId: string;
  fieldId?: string | null;
  fieldPath: string;
  fieldType: string;
  rawValue?: unknown;
  normalizedValue?: string | null;
  displayValue?: string | null;
  normalizedJson?: Record<string, unknown> | null;
  metadataJson?: Record<string, unknown> | null;
  confidence: number;
  status: string;
  evidenceId?: string | null;
  isRequired: boolean;
  itemIndex?: number | null;
}

export interface ExtractedObject {
  objectId: string;
  extractionResultId: string;
  parentObjectId?: string | null;
  fieldPath: string;
  fieldType: string;
  objectType?: string | null;
  itemIndex?: number | null;
  status: string;
}

export interface ExtractionEvidence {
  evidenceId: string;
  evidenceType: string;
  pageNumber?: number | null;
  bboxJson?: Record<string, unknown> | null;
  sheetName?: string | null;
  cellRange?: string | null;
  sourceText?: string | null;
  sourceValue?: unknown;
  ruleId?: string | null;
  ruleStrategy?: string | null;
  confidence?: number | null;
}

export const extractionReviewApi = {
  latestResult(documentId: string) {
    return apiRequest<ExtractionResultSummary>(`/documents/${documentId}/extraction-result`);
  },

  listFields(resultId: string, params: { status?: string; fieldType?: string; requiresReview?: boolean; minConfidence?: number } = {}) {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.fieldType) query.set("field_type", params.fieldType);
    if (params.requiresReview !== undefined) query.set("requires_review", String(params.requiresReview));
    if (params.minConfidence !== undefined) query.set("min_confidence", String(params.minConfidence));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiRequest<{ items: ExtractedFieldValue[] }>(`/extractions/results/${resultId}/fields${suffix}`);
  },

  listObjects(resultId: string) {
    return apiRequest<{ items: ExtractedObject[] }>(`/extractions/results/${resultId}/objects`);
  },

  listArrayItems(resultId: string, fieldPath: string) {
    return apiRequest<{ items: Array<{ arrayItemId: string; itemIndex: number; status: string; confidence: number }> }>(
      `/extractions/results/${resultId}/array-items?field_path=${encodeURIComponent(fieldPath)}`,
    );
  },

  listEvidence(fieldValueId: string) {
    return apiRequest<{ items: ExtractionEvidence[] }>(`/extractions/fields/${fieldValueId}/evidence`);
  },

  correctField(fieldValueId: string, rawValue: unknown, reason?: string) {
    return apiRequest<ExtractedFieldValue>(`/extractions/fields/${fieldValueId}/correction`, {
      method: "PATCH",
      body: JSON.stringify({ rawValue, reason }),
    });
  },

  approveField(fieldValueId: string, reason?: string) {
    return apiRequest<ExtractedFieldValue>(`/extractions/fields/${fieldValueId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },

  rejectField(fieldValueId: string, reason?: string) {
    return apiRequest<ExtractedFieldValue>(`/extractions/fields/${fieldValueId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },

  approveResult(resultId: string, reason?: string) {
    return apiRequest<ExtractionResultSummary>(`/extractions/results/${resultId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },
};

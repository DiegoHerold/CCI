import { apiRequest } from "@/lib/api/http-client";
import type { DocumentSelection } from "@/features/document-viewer/types/selection";
import type {
  AnnotationWithRuleResponse,
  ExtractionStrategy,
  ExtractionRule,
  FieldType,
  IdentificationSignal,
  TemplateAnnotation,
  TemplateBuilderState,
  TemplateCategory,
  TemplateSuggestionResponse,
  TemplateField,
  TemplateFileFormat,
  TemplateSummary,
  TemplateVersion,
  TemplateStructureType,
  RulePreviewNormalizationResponse,
} from "../types/templateBuilder";

function jsonBody(payload: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(payload) };
}

export const templateBuilderApi = {
  listTemplates() {
    return apiRequest<{ items: TemplateSummary[]; total: number }>("/templates");
  },

  listCategories() {
    return apiRequest<{ items: TemplateCategory[] }>("/template-categories");
  },

  createTemplate(payload: {
    name: string;
    description?: string | null;
    categoryId: string;
    fileFormat: TemplateFileFormat;
    structureType: TemplateStructureType;
  }) {
    return apiRequest<TemplateSummary>("/templates", jsonBody(payload));
  },

  getBuilderState(templateId: string) {
    return apiRequest<TemplateBuilderState>(`/templates/${templateId}/builder-state`);
  },

  createField(templateId: string, payload: {
    fieldPath: string;
    label: string;
    fieldType: FieldType;
    isRequired?: boolean;
    important?: boolean;
    isRepeated?: boolean;
    isObject?: boolean;
    isArray?: boolean;
    orderIndex?: number;
  }) {
    return apiRequest<TemplateField>(`/templates/${templateId}/fields`, jsonBody(payload));
  },

  createExtractionRule(templateId: string, payload: {
    fieldId: string;
    ruleType?: string | null;
    strategy: ExtractionStrategy;
    config: Record<string, unknown>;
    confidenceHint?: number | null;
    createdFromAnnotationId?: string | null;
  }) {
    return apiRequest<ExtractionRule>(`/templates/${templateId}/extraction-rules`, jsonBody(payload));
  },

  deleteAnnotation(templateId: string, annotationId: string) {
    return apiRequest<void>(`/templates/${templateId}/annotations/${annotationId}`, { method: "DELETE" });
  },

  createAnnotationWithRule(templateId: string, payload: {
    fieldId: string;
    documentId: string;
    sourcePreviewId?: string | null;
    annotationType: DocumentSelection["selection_type"];
    selectedText?: string | null;
    selectionPayload: DocumentSelection;
    generateRule: boolean;
    ruleStrategy?: ExtractionStrategy | null;
    ruleConfig?: Record<string, unknown> | null;
  }) {
    return apiRequest<AnnotationWithRuleResponse>(`/templates/${templateId}/annotations/with-rule`, jsonBody(payload));
  },

  createSignal(templateId: string, payload: {
    signalType: string;
    value: string;
    weight: number;
    required: boolean;
    negative: boolean;
  }) {
    return apiRequest<IdentificationSignal>(`/templates/${templateId}/identification-signals`, jsonBody(payload));
  },

  createVersion(templateId: string) {
    return apiRequest<TemplateVersion>(`/templates/${templateId}/versions`, jsonBody({}));
  },

  publishVersion(templateId: string, versionId: string) {
    return apiRequest<{ templateId: string; versionId: string; versionNumber: number; status: string; active: boolean }>(
      `/templates/${templateId}/versions/${versionId}/publish`,
      { method: "POST" },
    );
  },

  listAnnotations(templateId: string) {
    return apiRequest<{ items: TemplateAnnotation[] }>(`/templates/${templateId}/annotations`);
  },

  suggestFromDocument(documentId: string) {
    return apiRequest<TemplateSuggestionResponse>(`/templates/from-document/${documentId}/suggestions`, { method: "POST", body: JSON.stringify({}) });
  },

  previewNormalization(templateId: string, payload: {
    documentId: string;
    fieldPath: string;
    fieldType: FieldType;
    rule: Record<string, unknown>;
  }) {
    return apiRequest<RulePreviewNormalizationResponse>(`/templates/${templateId}/rules/preview-normalization`, jsonBody(payload));
  },
};

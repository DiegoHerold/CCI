export type EventType =
  | "DocumentUploaded" | "DocumentDuplicateDetected" | "DocumentRejected"
  | "DocumentStorageFailed" | "DocumentPreviewRequested" | "DocumentPreviewStarted"
  | "DocumentPreviewGenerated" | "DocumentPreviewFailed"
  | "TemplateCategoryCreated" | "TemplateCreated" | "TemplateUpdated"
  | "TemplateFieldCreated" | "TemplateIdentificationSignalCreated"
  | "TemplateAnnotationCreated" | "TemplateAnnotationUpdated" | "TemplateExtractionRuleCreated"
  | "TemplateVersionCreated" | "TemplateVersionPublished" | "TemplateArchived"
  | "TemplateMatched" | "TemplateNotFound" | "TemplateAmbiguous" | "TemplateManuallyConfirmed"
  | "ExtractionRequested" | "ExtractionStarted" | "ExtractionWorkerDispatched"
  | "ExtractionCompleted" | "ExtractionFailed" | "ExtractionRetryScheduled"
  | "ExtractionCancelled" | "ExtractionReviewed"
  | "ExtractionNormalizationStarted" | "ExtractionNormalizationCompleted"
  | "ExtractionNormalizationFailed" | "ExtractionResultsSaved" | "ExtractionRequiresReview"
  | "ExtractionFieldCorrected" | "ExtractionFieldApproved" | "ExtractionFieldRejected"
  | "ExtractionResultApproved"
  | "RulePublished" | "RuleExecutionCompleted"
  | "ConferenceStarted" | "ConferenceCompleted"
  | "ReportRequested" | "ReportGenerated"
  | "file.imported" | "document.classified" | "document.ambiguous"
  | "document.missing" | "document.confirmed" | "extraction.started"
  | "raw.extracted" | "variables.normalized" | "variables.ready"
  | "variables.need_review" | "schedule.due" | "folder.ready"
  | "execution.started" | "rule.executed" | "result.created"
  | "divergence.found" | "execution.finished" | "audit.created"
  | "report.generated" | "log.created";

export interface EventEnvelope<TPayload extends Record<string, unknown>> {
  event_id: string;
  event_type: EventType;
  version: number;
  occurred_at: string;
  correlation_id: string;
  causation_id?: string | null;
  producer: string;
  client_id?: string | null;
  competence_id?: string | null;
  execution_id?: string | null;
  document_id?: string | null;
  payload: TPayload;
}

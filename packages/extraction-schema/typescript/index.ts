export type ExtractionJobStatus = "pending" | "queued" | "starting" | "running" | "waiting_worker" | "worker_running" | "completed" | "failed" | "cancelled" | "retrying" | "requires_review";
export interface ExtractionRequest { force_reprocess?: boolean; matching_run_id?: string | null; template_id?: string | null; template_version_id?: string | null }
export interface ExtractionJob { extraction_job_id: string; document_id: string; client_id: string; competence_id: string; template_id: string; template_version_id: string; matching_run_id?: string | null; file_format: string; status: ExtractionJobStatus; attempt_count: number; max_attempts: number; workflow_id?: string | null; workflow_run_id?: string | null; error_code?: string | null; error_message?: string | null }
export interface ExtractionAttempt { attempt_id: string; extraction_job_id: string; attempt_number: number; status: string; worker_type?: string | null; worker_name?: string | null; error_code?: string | null; error_message?: string | null }
export interface ExtractionArtifact { artifact_id: string; extraction_job_id: string; document_id: string; artifact_type: "worker_raw_output" | "workflow_log" | "debug_payload"; storage_bucket: string; storage_key: string; content_hash?: string | null }
export interface ExtractionWorkflowInput { extraction_job_id: string; document_id: string; client_id: string; competence_id: string; template_id: string; template_version_id: string; file_format: string }
export interface ExtractionWorkflowOutput { extraction_job_id: string; status: ExtractionJobStatus; artifact_id?: string | null }
export interface ExtractorWorkerInput { extraction_job_id: string; document: Record<string, unknown>; preview: Record<string, unknown>; template: Record<string, unknown> }
export interface ExtractorWorkerOutput { extraction_job_id: string; status: "completed" | "failed" | "requires_review"; raw_output: Record<string, unknown>; warnings: string[]; errors: string[] }
export interface ExtractionError { code: string; message: string }
export interface ExtractionRetryPolicy { max_attempts: number; initial_interval_seconds: number; backoff_coefficient: number; max_interval_seconds: number }

export interface ExtractedFieldValue { path: string; raw_value: unknown; normalized_value: unknown; value_type: string; confidence: number; evidence_ids: string[] }
export interface ExtractedObject { object_path: string; fields: ExtractedFieldValue[] }
export interface ExtractionResult { job_id: string; document_id: string; client_id: string; competence_id: string; template_id: string; template_version: number; status: "requested" | "running" | "review_required" | "completed" | "failed" | "cancelled"; review_status?: "not_required" | "pending" | "approved" | "corrected" | "rejected"; objects: ExtractedObject[]; error_code?: string | null }

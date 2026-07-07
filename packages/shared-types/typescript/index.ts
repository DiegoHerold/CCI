export type Role = "admin" | "coordinator" | "analyst" | "reviewer" | "read_only";
export type CompetenceStatus = "waiting_documents" | "documents_imported" | "documents_mapped" | "extracting" | "variables_ready" | "executing" | "finished" | "blocked" | "error";
export type DocumentType = "balancete" | "guia_inss" | "guia_fgts" | "folha_pagamento" | "relatorio_fiscal" | "relatorio_contabil" | "extrato" | "outro" | "desconhecido";
export type DocumentStatus = "imported" | "classified" | "ambiguous" | "missing" | "confirmed" | "rejected" | "extracted" | "error";
export type VariableStatus = "extracted" | "normalized" | "confirmed" | "corrected" | "ignored" | "need_review" | "used_in_rule";
export type RuleStatus = "draft" | "active" | "inactive" | "archived";
export type ExecutionStatus = "pending" | "running" | "paused" | "finished" | "failed" | "cancelled";
export type ResultStatus = "approved" | "divergent" | "error" | "pending" | "not_applicable" | "needs_review";
export type ReportStatus = "pending" | "generating" | "generated" | "failed";

export interface Permission { name: string }
export interface User { user_id: string; email: string; name: string; roles: Role[]; permissions: string[]; active: boolean }
export interface Client { client_id: string; name: string; cnpj?: string | null }
export interface Competence { competence_id: string; client_id: string; reference: string; status: CompetenceStatus }
export interface Document { document_id: string; client_id: string; competence_id: string; filename: string; document_type: DocumentType; status: DocumentStatus }
export interface Variable { variable_id: string; key: string; value: unknown; status: VariableStatus }
export interface Rule { rule_id: string; name: string; version: number; status: RuleStatus; logic: Record<string, unknown> }
export interface Execution { execution_id: string; client_id: string; competence_id: string; status: ExecutionStatus; started_at?: string | null; finished_at?: string | null }
export interface Result { result_id: string; execution_id: string; rule_id: string; status: ResultStatus; message?: string | null }
export interface AuditEntry { audit_id: string; action: string; occurred_at: string; actor_id: string; details: Record<string, unknown> }
export interface Report { report_id: string; execution_id: string; format: "pdf" | "xlsx" | "annotated_trial_balance"; status: ReportStatus; storage_key?: string | null }
export interface EventEnvelope<TPayload extends Record<string, unknown> = Record<string, unknown>> { event_id: string; event_type: string; version: number; occurred_at: string; correlation_id: string; producer: string; payload: TPayload }

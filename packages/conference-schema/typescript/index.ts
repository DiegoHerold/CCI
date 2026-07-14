export interface ExpectedDocument { category: string; template_id?: string | null; required: boolean }
export interface ConferenceResult { status: "approved" | "divergent" | "needs_review" | "error"; approved_count: number; divergent_count: number }
export interface TimelineEvent { event_type: string; occurred_at: string; actor_id?: string | null; correlation_id: string; details: Record<string, unknown> }
export interface ConferenceExecution { execution_id: string; model_id: string; client_id: string; competence_id: string; status: "pending" | "waiting_documents" | "running" | "review" | "completed" | "failed" | "cancelled"; expected_documents: ExpectedDocument[]; rule_versions: Array<{rule_id: string; version: number}>; result?: ConferenceResult | null; timeline: TimelineEvent[] }

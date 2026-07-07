export type DocumentType = "balancete" | "guia_inss" | "guia_fgts" | "folha_pagamento" | "relatorio_fiscal" | "relatorio_contabil" | "extrato" | "outro" | "desconhecido";
export type DocumentStatus = "imported" | "classified" | "ambiguous" | "missing" | "confirmed" | "rejected" | "extracted" | "error";

export interface BoundingBox { x: number; y: number; width: number; height: number }
export interface Evidence { document_id: string; page?: number | null; row?: number | null; column?: string | null; cell?: string | null; text?: string | null; bounding_box?: BoundingBox | null }
export interface Document { document_id: string; client_id: string; competence_id: string; filename: string; original_filename: string; extension: string; mime_type: string; size_bytes: number; sha256_hash: string; storage_bucket: string; storage_key: string; document_type: DocumentType; status: DocumentStatus; classification_confidence?: number | null; created_at: string; updated_at: string; metadata: Record<string, unknown> }

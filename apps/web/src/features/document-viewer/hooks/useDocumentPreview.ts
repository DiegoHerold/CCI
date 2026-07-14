"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/http-client";
import type { DocumentRecord, DocumentPreviewStatus, ParsedDocumentPreview } from "../types/preview";
import { documentPreviewApi } from "../services/documentPreviewApi";

export type DocumentViewerLoadState =
  | "loading_document"
  | "loading_preview"
  | "preview_missing"
  | "preview_pending"
  | "preview_processing"
  | "preview_ready"
  | "preview_failed"
  | "requires_ocr"
  | "unsupported_format"
  | "empty_preview"
  | "error";

export function useDocumentPreview(documentId: string) {
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [preview, setPreview] = useState<ParsedDocumentPreview | null>(null);
  const [status, setStatus] = useState<DocumentPreviewStatus | null>(null);
  const [state, setState] = useState<DocumentViewerLoadState>("loading_document");
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"request" | "reprocess" | null>(null);

  const deriveReadyState = useCallback((loadedPreview: ParsedDocumentPreview | null): DocumentViewerLoadState => {
    if (!loadedPreview) return "empty_preview";
    if (loadedPreview.file_format === "PDF" && loadedPreview.requires_ocr) return "requires_ocr";
    if (loadedPreview.file_format !== "PDF" && loadedPreview.file_format !== "XLSX" && loadedPreview.file_format !== "XLS") {
      return "unsupported_format";
    }
    if (loadedPreview.file_format === "PDF" && !loadedPreview.pages?.length) return "empty_preview";
    if ((loadedPreview.file_format === "XLSX" || loadedPreview.file_format === "XLS") && !loadedPreview.sheets?.length) {
      return "empty_preview";
    }
    return "preview_ready";
  }, []);

  const load = useCallback(async () => {
    setError(null);
    setState("loading_document");
    try {
      const loadedDocument = await documentPreviewApi.getDocument(documentId);
      setDocument(loadedDocument);
      setState("loading_preview");
      const previewStatus = await documentPreviewApi.getPreviewStatus(documentId);
      setStatus(previewStatus.status);

      if (previewStatus.status === "preview_pending") {
        setState("preview_pending");
        setPreview(null);
        return;
      }
      if (previewStatus.status === "preview_processing") {
        setState("preview_processing");
        setPreview(null);
        return;
      }
      if (previewStatus.status === "preview_failed") {
        setState("preview_failed");
        setError(previewStatus.errorMessage || "Não foi possível gerar preview deste documento.");
        setPreview(null);
        return;
      }
      if (previewStatus.status !== "preview_ready") {
        setState("preview_missing");
        setPreview(null);
        return;
      }

      const previewResponse = await documentPreviewApi.getPreview(documentId);
      setStatus(previewResponse.status);
      setPreview(previewResponse.preview);
      setState(deriveReadyState(previewResponse.preview));
    } catch (caught) {
      setPreview(null);
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Não foi possível carregar o documento.");
      }
      setState("error");
    }
  }, [deriveReadyState, documentId]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timeout);
  }, [load]);

  const requestPreview = useCallback(async () => {
    setBusyAction("request");
    setError(null);
    try {
      await documentPreviewApi.requestPreview(documentId);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Não foi possível solicitar o preview.");
      setState("error");
    } finally {
      setBusyAction(null);
    }
  }, [documentId, load]);

  const reprocessPreview = useCallback(async () => {
    setBusyAction("reprocess");
    setError(null);
    try {
      await documentPreviewApi.reprocessPreview(documentId);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Não foi possível reprocessar o preview.");
      setState("error");
    } finally {
      setBusyAction(null);
    }
  }, [documentId, load]);

  return {
    document,
    preview,
    status,
    state,
    error,
    busyAction,
    reload: load,
    requestPreview,
    reprocessPreview,
  };
}

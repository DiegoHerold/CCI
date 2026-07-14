"use client";

import { useCallback, useState } from "react";
import type { DocumentSelection } from "../types/selection";

export function useDocumentSelection() {
  const [selection, setSelection] = useState<DocumentSelection | null>(null);
  const clearSelection = useCallback(() => setSelection(null), []);
  return { selection, setSelection, clearSelection };
}

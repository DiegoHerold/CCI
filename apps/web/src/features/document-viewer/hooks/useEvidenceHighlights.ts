"use client";

import { useMemo } from "react";
import type { EvidenceHighlight } from "../types/selection";

export function useEvidenceHighlights(highlights: EvidenceHighlight[] = []) {
  return useMemo(() => highlights, [highlights]);
}

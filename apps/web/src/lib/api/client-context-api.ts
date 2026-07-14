import { apiRequest } from "./http-client";
import type { ClientContextResponse, Competency, PaginatedResponse } from "@/types/api";

export const clientContextApi = {
  get() {
    return apiRequest<ClientContextResponse>("/client-context");
  },

  updatePreference(defaultClientId: string, defaultCompetencePeriod?: string | null) {
    return apiRequest<{ defaultClientId: string | null; defaultCompetencePeriod: string | null }>(
      "/client-context/preferences",
      { method: "PATCH", body: JSON.stringify({ defaultClientId, ...(defaultCompetencePeriod ? { defaultCompetencePeriod } : {}) }) },
    );
  },

  listCompetencies(clientId: string) {
    return apiRequest<PaginatedResponse<Competency>>(
      `/clients/${encodeURIComponent(clientId)}/competencies?limit=50&sortDirection=desc`,
    );
  },

  ensureCurrentCompetency(clientId: string, period?: string | null) {
    const body = period && /^\d{4}-\d{2}$/.test(period)
      ? { year: Number(period.slice(0, 4)), month: Number(period.slice(5, 7)) }
      : {};
    return apiRequest<Competency>(
      `/clients/${encodeURIComponent(clientId)}/competencies/ensure-current`,
      { method: "POST", body: JSON.stringify(body) },
    );
  },
};

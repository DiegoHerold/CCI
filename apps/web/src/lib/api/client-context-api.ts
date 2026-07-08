import { apiRequest } from "./http-client";
import type { ClientContextResponse, Competency, PaginatedResponse } from "@/types/api";

export const clientContextApi = {
  get() {
    return apiRequest<ClientContextResponse>("/client-context");
  },

  updatePreference(defaultClientId: string) {
    return apiRequest<{ defaultClientId: string | null; defaultCompetencePeriod: string | null }>(
      "/client-context/preferences",
      { method: "PATCH", body: JSON.stringify({ defaultClientId }) },
    );
  },

  listCompetencies(clientId: string) {
    return apiRequest<PaginatedResponse<Competency>>(
      `/clients/${encodeURIComponent(clientId)}/competencies?limit=50&sortDirection=desc`,
    );
  },
};

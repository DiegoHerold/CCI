import { apiRequest } from "./http-client";
import type { ClientRecord, CreateClientPayload, PaginatedResponse } from "@/types/api";

export interface ListClientsParams {
  search?: string;
  page?: number;
  limit?: number;
}

function buildQuery(params: ListClientsParams) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  query.set("page", String(params.page ?? 1));
  query.set("limit", String(params.limit ?? 20));
  return query.toString();
}

export const clientsApi = {
  list(params: ListClientsParams = {}) {
    return apiRequest<PaginatedResponse<ClientRecord>>(`/clients?${buildQuery(params)}`);
  },

  create(payload: CreateClientPayload) {
    return apiRequest<ClientRecord>("/clients", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

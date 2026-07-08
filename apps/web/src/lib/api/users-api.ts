import { apiRequest } from "./http-client";
import type { InviteUserPayload, PaginatedResponse, UserRecord } from "@/types/api";

export interface ListUsersParams {
  search?: string;
  page?: number;
  limit?: number;
}

function buildQuery(params: ListUsersParams) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  query.set("page", String(params.page ?? 1));
  query.set("limit", String(params.limit ?? 20));
  return query.toString();
}

export const usersApi = {
  list(params: ListUsersParams = {}) {
    return apiRequest<PaginatedResponse<UserRecord>>(`/users?${buildQuery(params)}`);
  },

  invite(payload: InviteUserPayload) {
    return apiRequest<UserRecord>("/users/invitations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  resendInvite(userId: string) {
    return apiRequest<{ success?: boolean }>(`/users/${encodeURIComponent(userId)}/resend-invite`, {
      method: "POST",
    });
  },

  disable(userId: string) {
    return apiRequest<UserRecord>(`/users/${encodeURIComponent(userId)}/disable`, {
      method: "PATCH",
    });
  },
};

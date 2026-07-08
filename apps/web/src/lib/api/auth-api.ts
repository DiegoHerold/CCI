import { apiRequest, refreshAccessToken, setAccessToken } from "./http-client";
import type {
  AcceptInvitationPayload,
  AuthUser,
  InvitationDetails,
  LoginRequest,
  LoginResponse,
} from "@/types/api";

export const authApi = {
  async login(payload: LoginRequest) {
    const response = await apiRequest<LoginResponse>(
      "/auth/login",
      { method: "POST", body: JSON.stringify(payload) },
      { authenticated: false },
    );
    setAccessToken(response.accessToken);
    return response;
  },

  me() {
    return apiRequest<AuthUser>("/auth/me", {}, { retryOnUnauthorized: false });
  },

  refresh: refreshAccessToken,

  async logout() {
    try {
      await apiRequest<{ success?: boolean }>(
        "/auth/logout",
        { method: "POST" },
        { retryOnUnauthorized: false },
      );
    } finally {
      setAccessToken(null);
    }
  },

  getInvitation(token: string) {
    return apiRequest<InvitationDetails>(
      `/auth/invitations/${encodeURIComponent(token)}`,
      {},
      { authenticated: false },
    );
  },

  acceptInvitation(token: string, payload: AcceptInvitationPayload) {
    return apiRequest<{ success: boolean }>(
      `/auth/invitations/${encodeURIComponent(token)}/accept`,
      { method: "POST", body: JSON.stringify(payload) },
      { authenticated: false },
    );
  },
};

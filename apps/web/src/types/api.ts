export interface AuthUser {
  id: string;
  name: string;
  email: string;
  status: string;
  roles: string[];
  permissions: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginResponse extends TokenResponse {
  user: AuthUser;
}

export interface ClientSummary {
  id: string;
  code: string | null;
  name: string;
  tradeName: string | null;
  cnpj: string;
  status: "ACTIVE" | "INACTIVE" | "ARCHIVED";
  userClientRole: string | null;
  responsibilityArea: string | null;
  isPrimaryResponsible: boolean | null;
}

export interface CurrentCompetence {
  period: string;
  year: number;
  month: number;
}

export interface ClientContextResponse {
  user: AuthUser;
  clients: ClientSummary[];
  defaultClientId: string | null;
  currentCompetence: CurrentCompetence;
}

export interface Competency {
  id: string;
  clientId: string;
  period: string;
  year: number;
  month: number;
  status: string;
  folderPath: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
}

export interface BffErrorPayload {
  error?: {
    code?: string;
    message?: string;
    correlation_id?: string;
  };
  detail?: string;
}

export type ApiErrorCode =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "SERVICE_UNAVAILABLE"
  | "NETWORK_ERROR"
  | "UNKNOWN_ERROR";

export type ClientStatus = "ACTIVE" | "INACTIVE" | "ARCHIVED";

export interface ClientRecord {
  id: string;
  code: string | null;
  name: string;
  tradeName: string | null;
  cnpj: string;
  status: ClientStatus;
  taxRegime?: string | null;
  city?: string | null;
  state?: string | null;
  defaultFolderPath?: string | null;
  competenceFolderPattern?: string | null;
  notes?: string | null;
}

export interface CreateClientPayload {
  code?: string;
  name: string;
  tradeName?: string;
  cnpj: string;
  taxRegime?: string;
  city?: string;
  state?: string;
  defaultFolderPath?: string;
  competenceFolderPattern?: string;
  notes?: string;
}

export type UserStatus = "ACTIVE" | "INACTIVE" | "PENDING_INVITE" | "INVITE_EXPIRED" | "BLOCKED";

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  status: UserStatus;
  roles: string[];
  createdAt?: string;
  updatedAt?: string;
  inviteSentAt?: string | null;
  inviteAcceptedAt?: string | null;
}

export interface InviteUserPayload {
  name: string;
  email: string;
  roles: string[];
  clientIds?: string[];
}

export interface InvitationDetails {
  email: string;
  name: string;
  status: "VALID" | "EXPIRED" | "INVALID";
  expiresAt?: string;
}

export interface AcceptInvitationPayload {
  password: string;
  confirmPassword: string;
}

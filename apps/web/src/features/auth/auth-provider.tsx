"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { authApi } from "@/lib/api/auth-api";
import { setAccessToken, setSessionExpiredHandler } from "@/lib/api/http-client";
import type { AuthUser, LoginRequest } from "@/types/api";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: AuthUser | null;
  status: AuthStatus;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  retrySession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const started = useRef(false);

  const expireSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const loadSession = useCallback(async () => {
    setStatus("loading");
    try {
      await authApi.refresh();
      const currentUser = await authApi.me();
      setUser(currentUser);
      setStatus("authenticated");
    } catch {
      expireSession();
    }
  }, [expireSession]);

  useEffect(() => {
    setSessionExpiredHandler(expireSession);
    if (!started.current) {
      started.current = true;
      void loadSession();
    }
    return () => setSessionExpiredHandler(null);
  }, [expireSession, loadSession]);

  const login = useCallback(async (credentials: LoginRequest) => {
    setStatus("loading");
    try {
      await authApi.login(credentials);
      const currentUser = await authApi.me();
      setUser(currentUser);
      setStatus("authenticated");
    } catch (error) {
      expireSession();
      throw error;
    }
  }, [expireSession]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      expireSession();
    }
  }, [expireSession]);

  const value = useMemo(
    () => ({ user, status, login, logout, retrySession: loadSession }),
    [user, status, login, logout, loadSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

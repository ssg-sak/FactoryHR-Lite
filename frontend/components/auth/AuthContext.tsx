"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, setUnauthorizedHandler } from "@/lib/api";
import { clearStoredToken, getStoredToken, type AuthUser } from "@/lib/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isReady: boolean;
  canWrite: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  initialUser = undefined,
}: {
  children: ReactNode;
  initialUser?: AuthUser | null;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(initialUser ?? null);
  const [isReady, setIsReady] = useState(initialUser !== undefined);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    if (pathname !== "/login") {
      router.replace("/login");
    }
  }, [pathname, router]);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  useEffect(() => {
    if (initialUser !== undefined) {
      return;
    }
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setIsReady(true);
      return;
    }
    let cancelled = false;
    api
      .me()
      .then((current) => {
        if (!cancelled) {
          setUser(current);
        }
      })
      .catch(() => {
        if (!cancelled) {
          clearStoredToken();
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsReady(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [initialUser]);

  const login = useCallback(async (username: string, password: string) => {
    const result = await api.login(username, password);
    setUser(result.user);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isReady,
      canWrite: user?.role === "admin",
      login,
      logout,
    }),
    [isReady, login, logout, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}

export { AuthContext };

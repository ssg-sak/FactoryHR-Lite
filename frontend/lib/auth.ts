export type UserRole = "viewer" | "admin";

export interface AuthUser {
  username: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const TOKEN_KEY = "factoryhr.access_token";

// Portfolio/demo: JWT is stored in localStorage so the split Render frontend/API
// hosts can send Authorization headers. This is XSS-sensitive and is not SSO/MFA.

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export const DEMO_VIEWER_USERNAME = "viewer";
export const DEMO_VIEWER_PASSWORD = "viewer-demo";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { AuthProvider } from "@/components/auth/AuthContext";
import { WorkforceFilterProvider } from "@/components/filters/WorkforceFilterContext";
import type { AuthUser } from "@/lib/auth";

export const TEST_ADMIN: AuthUser = { username: "admin", role: "admin" };
export const TEST_VIEWER: AuthUser = { username: "viewer", role: "viewer" };

export function renderWithQuery(
  ui: ReactElement,
  options?: { user?: AuthUser | null },
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const user = options && "user" in options ? options.user : TEST_ADMIN;
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider initialUser={user}>
        <WorkforceFilterProvider>{ui}</WorkforceFilterProvider>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

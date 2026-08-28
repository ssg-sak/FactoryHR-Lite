import { ApiError, formatApiError } from "./errors";
import {
  clearStoredToken,
  getStoredToken,
  setStoredToken,
  type AuthUser,
  type LoginResponse,
} from "./auth";
import type {
  AIReportResponse,
  Attendance,
  AttendanceListResponse,
  AttendanceTrend,
  AttendanceWritePayload,
  DashboardSummary,
  DataQualityResult,
  Department,
  Employee,
  EmployeeListResponse,
  EmployeeWritePayload,
  Factory,
  OvertimeSummary,
  ProductionLine,
  Shift,
  TenureDistribution,
  WorkforceDistribution,
  WorkforceFilters,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function toQuery(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

export function workforceQuery(filters: WorkforceFilters): Record<string, string | number | undefined> {
  return {
    date_from: filters.date_from,
    date_to: filters.date_to,
    department_id: filters.department_id,
    factory_id: filters.factory_id,
    production_line_id: filters.production_line_id,
    shift_id: filters.shift_id,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });
  if (response.status === 401) {
    clearStoredToken();
    unauthorizedHandler?.();
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = isJson ? (body as { detail?: unknown }).detail : body;
    throw new ApiError(formatApiError(response.status, detail), response.status);
  }
  return body as T;
}

export const api = {
  health: () => request<{ status: string; database: string }>("/health"),
  login: async (username: string, password: string) => {
    const result = await request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setStoredToken(result.access_token);
    return result;
  },
  me: () => request<AuthUser>("/auth/me"),
  departments: () => request<Department[]>("/api/departments"),
  factories: () => request<Factory[]>("/api/factories"),
  productionLines: (factoryId?: number) =>
    request<ProductionLine[]>(`/api/production-lines${toQuery({ factory_id: factoryId })}`),
  shifts: () => request<Shift[]>("/api/shifts"),
  employees: (params: Record<string, string | number | undefined>) =>
    request<EmployeeListResponse>(`/api/employees${toQuery(params)}`),
  employee: (id: number) => request<Employee>(`/api/employees/${id}`),
  createEmployee: (payload: EmployeeWritePayload) =>
    request<Employee>("/api/employees", { method: "POST", body: JSON.stringify(payload) }),
  updateEmployee: (id: number, payload: Partial<EmployeeWritePayload>) =>
    request<Employee>(`/api/employees/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteEmployee: (id: number) =>
    request<void>(`/api/employees/${id}`, { method: "DELETE" }),
  attendance: (params: Record<string, string | number | undefined>) =>
    request<AttendanceListResponse>(`/api/attendance${toQuery(params)}`),
  createAttendance: (payload: AttendanceWritePayload) =>
    request<Attendance>("/api/attendance", { method: "POST", body: JSON.stringify(payload) }),
  updateAttendance: (id: number, payload: Partial<AttendanceWritePayload>) =>
    request<Attendance>(`/api/attendance/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteAttendance: (id: number) =>
    request<void>(`/api/attendance/${id}`, { method: "DELETE" }),
  dashboardSummary: (filters: WorkforceFilters) =>
    request<DashboardSummary>(`/api/dashboard/summary${toQuery(workforceQuery(filters))}`),
  workforceDistribution: (filters: WorkforceFilters) =>
    request<WorkforceDistribution>(
      `/api/dashboard/workforce-distribution${toQuery(workforceQuery(filters))}`,
    ),
  attendanceTrend: (filters: WorkforceFilters) =>
    request<AttendanceTrend>(`/api/dashboard/attendance-trend${toQuery(workforceQuery(filters))}`),
  overtime: (filters: WorkforceFilters) =>
    request<OvertimeSummary>(`/api/dashboard/overtime${toQuery(workforceQuery(filters))}`),
  tenure: (filters: WorkforceFilters) =>
    request<TenureDistribution>(
      `/api/dashboard/tenure-distribution${toQuery(workforceQuery(filters))}`,
    ),
  dataQuality: () => request<DataQualityResult>("/api/dashboard/data-quality"),
  aiSummary: (filters: WorkforceFilters) =>
    request<AIReportResponse>(`/api/reports/ai-summary${toQuery(workforceQuery(filters))}`, {
      method: "POST",
    }),
};

export async function downloadReport(
  path: "/api/reports/workforce.pdf" | "/api/reports/employees.csv" | "/api/reports/attendance.csv",
  filters: WorkforceFilters,
): Promise<void> {
  const response = await fetch(`${API_URL}${path}${toQuery(workforceQuery(filters))}`, {
    headers: authHeaders(),
  });
  if (response.status === 401) {
    clearStoredToken();
    unauthorizedHandler?.();
  }
  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    const body = contentType.includes("application/json") ? await response.json() : await response.text();
    const detail = contentType.includes("application/json")
      ? (body as { detail?: unknown }).detail
      : body;
    throw new ApiError(formatApiError(response.status, detail), response.status);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? path.split("/").pop() ?? "download";
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

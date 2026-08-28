import type { ReactNode } from "react";
import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import EmployeesPage from "@/app/employees/page";
import { jsonResponse, renderWithQuery, TEST_VIEWER } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/employees",
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), prefetch: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function employeeListResponse() {
  return jsonResponse({
    items: [
      {
        id: 1,
        employee_number: "FHR-0001",
        name: "김민준",
        department_id: 1,
        department_name: "생산",
        factory_id: 1,
        factory_name: "대구1공장",
        production_line_id: 1,
        production_line_name: "조립 A라인",
        shift_id: 1,
        shift_name: "주간조",
        position: "사원",
        hired_at: "2024-01-01",
        resigned_at: null,
        status: "active",
        created_at: "2026-01-01T00:00:00",
        updated_at: "2026-01-01T00:00:00",
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  });
}

describe("EmployeesPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the employee table", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse([]);
        }
        if (url.includes("/api/employees")) {
          return employeeListResponse();
        }
        return jsonResponse({});
      }),
    );
    renderWithQuery(<EmployeesPage />);
    expect(await screen.findByText("FHR-0001")).toBeInTheDocument();
    expect(screen.getByText("김민준")).toBeInTheDocument();
    expect(screen.getByText("대구1공장")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "직원 등록" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "수정" })).toBeInTheDocument();
  });

  it("hides write actions for viewer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse([]);
        }
        if (url.includes("/api/employees")) {
          return employeeListResponse();
        }
        return jsonResponse({});
      }),
    );
    renderWithQuery(<EmployeesPage />, { user: TEST_VIEWER });
    expect(await screen.findByText("FHR-0001")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "직원 등록" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "수정" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "삭제" })).not.toBeInTheDocument();
  });

  it("shows empty state when the list is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse([]);
        }
        return jsonResponse({ items: [], total: 0, page: 1, page_size: 20 });
      }),
    );
    renderWithQuery(<EmployeesPage />);
    expect(await screen.findByText("선택한 조건에 해당하는 데이터가 없습니다.")).toBeInTheDocument();
  });
});

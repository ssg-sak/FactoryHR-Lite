import type { ReactNode } from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "@/app/dashboard/page";
import { jsonResponse, renderWithQuery } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const emptyMaster: unknown[] = [];

function dashboardPayload() {
  return {
    date_from: "2026-07-29",
    date_to: "2026-08-27",
    active_employees: 46,
    resigned_in_period: 4,
    average_tenure_months: 18.2,
    average_overtime_hours: 0.8,
    absence_rate: 3.1,
    late_rate: 7.4,
    attendance_records: 1070,
    metric_definitions: {
      active_employees: "status=active 인 직원 수 (현재 재직)",
      absence_rate: "선택 기간 attendance 중 attendance_status=absent 비율(%)",
    },
    employees_by_factory: [],
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders KPI cards from the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse(emptyMaster);
        }
        if (url.includes("/summary")) return jsonResponse(dashboardPayload());
        if (url.includes("/workforce-distribution")) {
          return jsonResponse({
            active_by_factory: [{ id: 1, code: "DAEGU", name: "대구1공장", count: 24 }],
            active_by_line: [],
            active_by_shift: [],
            resignations_by_department: [],
            resignations_by_line: [],
          });
        }
        if (url.includes("/attendance-trend")) return jsonResponse({ points: [] });
        if (url.includes("/overtime")) return jsonResponse({ by_production_line: [], by_shift: [] });
        if (url.includes("/tenure-distribution")) {
          return jsonResponse({
            report_date: "2026-08-27",
            bands: [{ key: "12_36", label: "1~3년", count: 20 }],
            definition: "재직 직원만",
          });
        }
        if (url.includes("/data-quality")) {
          return jsonResponse({
            total_employees: 50,
            total_attendance_records: 1070,
            duplicate_employee_numbers: 0,
            duplicate_attendance: 0,
            invalid_work_hours: 0,
            invalid_overtime_hours: 0,
            attendance_before_hire_date: 0,
            attendance_after_resignation: 0,
            factory_line_mismatch: 0,
          });
        }
        return jsonResponse({});
      }),
    );

    const user = userEvent.setup();
    renderWithQuery(<DashboardPage />);
    expect(await screen.findByText("현재 재직 인원")).toBeInTheDocument();
    expect(await screen.findByText("46")).toBeInTheDocument();
    expect(screen.getByText("현재 재직 상태인 직원 수")).toBeInTheDocument();
    expect(screen.getByText("데이터 검증 상태")).toBeInTheDocument();
    expect(screen.getByText("주요 정합성 검사 통과")).toBeInTheDocument();
    expect(screen.getByText("공장별 재직 인원")).toBeInTheDocument();
    expect(screen.queryByText("status = active인 직원 수")).not.toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "지표 정의" })[0]);
    expect(screen.getByText("status = active인 직원 수")).toBeInTheDocument();
  });

  it("shows an API error state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse([]);
        }
        if (url.includes("/summary")) {
          return jsonResponse({ detail: "date_from cannot be after date_to" }, 400);
        }
        return jsonResponse({});
      }),
    );
    renderWithQuery(<DashboardPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("시작일은 종료일보다 늦을 수 없습니다.");
  });

  it("shows empty chart state when there is no data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments") || url.includes("/api/factories") || url.includes("/api/shifts") || url.includes("/api/production-lines")) {
          return jsonResponse([]);
        }
        if (url.includes("/summary")) return jsonResponse(dashboardPayload());
        if (url.includes("/workforce-distribution")) {
          return jsonResponse({
            active_by_factory: [],
            active_by_line: [],
            active_by_shift: [],
            resignations_by_department: [],
            resignations_by_line: [],
          });
        }
        if (url.includes("/attendance-trend")) return jsonResponse({ points: [] });
        if (url.includes("/overtime")) return jsonResponse({ by_production_line: [], by_shift: [] });
        if (url.includes("/tenure-distribution")) {
          return jsonResponse({ report_date: "2026-08-27", bands: [], definition: "" });
        }
        if (url.includes("/data-quality")) {
          return jsonResponse({
            total_employees: 0,
            total_attendance_records: 0,
            duplicate_employee_numbers: 0,
            duplicate_attendance: 0,
            invalid_work_hours: 0,
            invalid_overtime_hours: 0,
            attendance_before_hire_date: 0,
            attendance_after_resignation: 0,
            factory_line_mismatch: 0,
          });
        }
        return jsonResponse({});
      }),
    );
    renderWithQuery(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getAllByText("선택한 조건에 해당하는 데이터가 없습니다.").length).toBeGreaterThan(0);
    });
  });

  it("updates the filter summary when a factory is selected", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/departments")) return jsonResponse([]);
        if (url.includes("/api/factories")) {
          return jsonResponse([{ id: 1, code: "DAEGU", name: "대구1공장", location: null }]);
        }
        if (url.includes("/api/shifts") || url.includes("/api/production-lines")) return jsonResponse([]);
        if (url.includes("/summary")) return jsonResponse(dashboardPayload());
        if (url.includes("/workforce-distribution")) {
          return jsonResponse({
            active_by_factory: [],
            active_by_line: [],
            active_by_shift: [],
            resignations_by_department: [],
            resignations_by_line: [],
          });
        }
        if (url.includes("/attendance-trend")) return jsonResponse({ points: [] });
        if (url.includes("/overtime")) return jsonResponse({ by_production_line: [], by_shift: [] });
        if (url.includes("/tenure-distribution")) {
          return jsonResponse({ report_date: "2026-08-27", bands: [], definition: "" });
        }
        if (url.includes("/data-quality")) {
          return jsonResponse({
            total_employees: 50,
            total_attendance_records: 1070,
            duplicate_employee_numbers: 0,
            duplicate_attendance: 0,
            invalid_work_hours: 0,
            invalid_overtime_hours: 0,
            attendance_before_hire_date: 0,
            attendance_after_resignation: 0,
            factory_line_mismatch: 0,
          });
        }
        return jsonResponse({});
      }),
    );
    renderWithQuery(<DashboardPage />);
    expect(await screen.findByRole("option", { name: "대구1공장" })).toBeInTheDocument();
    const factory = screen.getByLabelText("공장");
    await user.selectOptions(factory, "1");
    expect(screen.getByTestId("filter-summary")).toHaveTextContent("대구1공장");
  });
});

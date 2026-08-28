import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { EmployeeForm } from "@/components/employees/EmployeeForm";
import { jsonResponse, renderWithQuery } from "./test-utils";

describe("EmployeeForm", () => {
  it("validates required fields and resignation date", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse([])),
    );
    const onSubmit = vi.fn();
    renderWithQuery(
      <EmployeeForm submitting={false} error={null} onSubmit={onSubmit} onCancel={() => undefined} />,
    );
    await user.click(screen.getByRole("button", { name: "저장" }));
    expect(await screen.findByText("사번을 입력하세요.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText("사번"), "FHR-0100");
    await user.type(screen.getByLabelText("이름"), "테스트");
    await user.type(screen.getByLabelText("입사일"), "2026-08-01");
    await user.selectOptions(screen.getByLabelText("상태"), "resigned");
    await user.click(screen.getByRole("button", { name: "저장" }));
    expect(await screen.findByText("퇴사 직원은 퇴사일이 필요합니다.")).toBeInTheDocument();
  });
});

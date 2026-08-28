import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "@/app/login/page";
import { jsonResponse, renderWithQuery } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/login",
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), prefetch: vi.fn() }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the login form without a signup action", () => {
    renderWithQuery(<LoginPage />, { user: null });
    expect(screen.getByRole("heading", { name: "로그인" })).toBeInTheDocument();
    expect(screen.getByLabelText("사용자 이름")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toBeInTheDocument();
    expect(screen.getByText(/공개 회원가입을 제공하지 않습니다/)).toBeInTheDocument();
    expect(screen.getByText(/DEMO ACCOUNT/)).toBeInTheDocument();
    expect(screen.queryByText("회원가입")).not.toBeInTheDocument();
  });

  it("shows an error when login fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({ detail: "Invalid username or password" }, 401),
      ),
    );
    renderWithQuery(<LoginPage />, { user: null });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("사용자 이름"), "admin");
    await user.type(screen.getByLabelText("비밀번호"), "wrong");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    expect(
      await screen.findByText("사용자 이름 또는 비밀번호가 올바르지 않습니다."),
    ).toBeInTheDocument();
  });
});

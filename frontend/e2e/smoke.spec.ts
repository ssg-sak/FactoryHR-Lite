import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const images = path.resolve(__dirname, "../../docs/images");
const username = process.env.E2E_USERNAME ?? "admin";
const password = process.env.E2E_PASSWORD ?? "admin-local";

async function hideDevOverlay(page: Page) {
  await page.addStyleTag({
    content: "nextjs-portal, [data-next-badge-root] { display: none !important; }",
  });
}

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("사용자 이름").fill(username);
  await page.getByLabel("비밀번호").fill(password);
  await page.getByRole("button", { name: "로그인" }).click();
  await expect(page.getByText("현재 재직 인원")).toBeVisible({ timeout: 20_000 });
}

test.describe("FactoryHR Lite smoke", () => {
  test("dashboard loads KPIs and data quality", async ({ page }) => {
    await login(page);
    await expect(page.getByText("데이터 검증 상태")).toBeVisible();
    await expect(page.getByText("주요 정합성 검사 통과")).toBeVisible();
    await hideDevOverlay(page);
    await page.screenshot({ path: path.join(images, "dashboard.png"), fullPage: false });
  });

  test("employees table loads and delete with attendance is blocked", async ({ page }) => {
    await login(page);
    await page.goto("/employees");
    await expect(page.getByText("FHR-0001")).toBeVisible({ timeout: 20_000 });
    await hideDevOverlay(page);
    await page.screenshot({ path: path.join(images, "employees.png"), fullPage: false });

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "삭제" }).first().click();
    await expect(page.getByText("근태 기록이 있는 직원은 삭제할 수 없습니다.")).toBeVisible({
      timeout: 10_000,
    });
  });

  test("attendance form blocks work hours over 16", async ({ page }) => {
    await login(page);
    await page.goto("/attendance");
    await page.getByRole("button", { name: "근태 등록" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.locator("label:has-text('근무시간') input").fill("17");
    await page.getByRole("button", { name: "저장" }).click();
    await expect(page.getByText("근무시간은 16시간을 넘을 수 없습니다.")).toBeVisible();
    await hideDevOverlay(page);
    await page.screenshot({ path: path.join(images, "attendance.png"), fullPage: false });
  });

  test("reports page exposes PDF download and shared filters", async ({ page }) => {
    await login(page);
    await expect(page.getByText("현재 재직 인원")).toBeVisible({ timeout: 20_000 });
    await page.getByLabel("공장").selectOption({ index: 1 });
    await expect(page.getByTestId("filter-summary")).not.toContainText("공장 전체");

    await page.getByRole("link", { name: "리포트" }).click();
    await expect(page.getByRole("button", { name: "PDF 리포트 다운로드" })).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByRole("button", { name: "직원 CSV" })).toBeVisible();
    await expect(page.getByRole("button", { name: "AI 요약 생성" })).toBeVisible();
    await expect(page.getByTestId("filter-summary")).not.toContainText("공장 전체");
    await hideDevOverlay(page);
    await page.screenshot({ path: path.join(images, "reports.png"), fullPage: false });
  });
});

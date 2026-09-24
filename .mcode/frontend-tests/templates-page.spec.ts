/**
 * templates-page.spec.ts
 *
 * Tests the Email Templates page (/templates).
 * The app seeds 4 default templates on first start.
 * Selectors from QA report DOM snapshot.
 */
import { test, expect } from "@playwright/test";

test.describe("Templates page (/templates)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/templates");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle("SMTP Testing Tool - Email Templates");
  });

  test("Email Templates card header is visible", async ({ page }) => {
    const header = page.locator(".card-header").filter({ hasText: "Email Templates" });
    await expect(header).toBeVisible();
  });

  test("card header h5 contains 'Email Templates'", async ({ page }) => {
    await expect(page.locator(".card-header h5")).toContainText("Email Templates");
  });

  test("card header has purple-to-blue gradient", async ({ page }) => {
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".card-header");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("Add Template button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "+ Add Template" })
    ).toBeVisible();
  });

  test("templates table has columns: Name, Subject, Type, Actions", async ({
    page,
  }) => {
    await expect(page.locator("th").filter({ hasText: "Name" })).toBeVisible();
    await expect(page.locator("th").filter({ hasText: "Subject" })).toBeVisible();
    await expect(page.locator("th").filter({ hasText: "Type" })).toBeVisible();
    await expect(page.locator("th").filter({ hasText: "Actions" })).toBeVisible();
  });

  test("4 default template rows are present", async ({ page }) => {
    const rows = page.locator("table tbody tr");
    await expect(rows).toHaveCount(4);
  });

  test("default template 'Plain Text Example' is in the table", async ({
    page,
  }) => {
    await expect(page.locator("table")).toContainText("Plain Text Example");
  });

  test("default template 'HTML Example' is in the table", async ({ page }) => {
    await expect(page.locator("table")).toContainText("HTML Example");
  });

  test("default template 'EICAR Antivirus Test' is in the table", async ({
    page,
  }) => {
    await expect(page.locator("table")).toContainText("EICAR Antivirus Test");
  });

  test("default template 'SPF Test' is in the table", async ({ page }) => {
    await expect(page.locator("table")).toContainText("SPF Test");
  });

  test("each template row has 3 action buttons", async ({ page }) => {
    const rows = page.locator("table tbody tr");
    const count = await rows.count();
    for (let i = 0; i < count; i++) {
      const actionBtns = rows.nth(i).locator("td:last-child button, td:last-child a");
      await expect(actionBtns).toHaveCount(3);
    }
  });
});

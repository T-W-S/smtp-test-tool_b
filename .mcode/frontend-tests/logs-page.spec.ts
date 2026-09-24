/**
 * logs-page.spec.ts
 *
 * Tests the Email Logs page (/logs).
 * Selectors from QA report DOM snapshot.
 */
import { test, expect } from "@playwright/test";

test.describe("Logs page (/logs)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/logs");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle("SMTP Testing Tool - Email Logs");
  });

  test("Email Sending Logs card header is visible", async ({ page }) => {
    const header = page
      .locator(".card-header")
      .filter({ hasText: "Email Sending Logs" });
    await expect(header).toBeVisible();
  });

  test("card header h5 contains 'Email Sending Logs'", async ({ page }) => {
    await expect(page.locator(".card-header h5")).toContainText(
      "Email Sending Logs"
    );
  });

  test("card header has purple-to-blue gradient", async ({ page }) => {
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".card-header");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("Clear Logs button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Clear Logs" })
    ).toBeVisible();
  });

  test("navbar link to Logs navigates correctly", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Logs" }).click();
    await expect(page).toHaveURL(/\/logs/);
    await expect(page.locator(".card-header h5")).toContainText(
      "Email Sending Logs"
    );
  });
});

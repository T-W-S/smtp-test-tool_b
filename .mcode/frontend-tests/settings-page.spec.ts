/**
 * settings-page.spec.ts
 *
 * Tests the SMTP Settings page (/settings).
 * Selectors from QA report DOM snapshot.
 */
import { test, expect } from "@playwright/test";

test.describe("Settings page (/settings)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/settings");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle("SMTP Testing Tool - SMTP Settings");
  });

  test("SMTP Profiles card header is visible", async ({ page }) => {
    const header = page.locator(".card-header").filter({ hasText: "SMTP Profiles" });
    await expect(header).toBeVisible();
  });

  test("card header h5 contains 'SMTP Profiles'", async ({ page }) => {
    await expect(page.locator(".card-header h5")).toContainText("SMTP Profiles");
  });

  test("card header has purple-to-blue gradient", async ({ page }) => {
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".card-header");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("Add Profile button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "+ Add Profile" })
    ).toBeVisible();
  });

  test("Advanced Settings link navigates to /advanced_settings", async ({
    page,
  }) => {
    const link = page.getByRole("link", { name: "Advanced Settings" });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/advanced_settings/);
  });

  test("navbar link to SMTP Settings is present", async ({ page }) => {
    await expect(
      page.getByRole("link", { name: "SMTP Settings" })
    ).toBeVisible();
  });
});

/**
 * advanced-settings-page.spec.ts
 *
 * Tests the Advanced Settings page (/advanced_settings).
 * Selectors and default values from QA report DOM snapshot.
 */
import { test, expect } from "@playwright/test";

test.describe("Advanced Settings page (/advanced_settings)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/advanced_settings");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle("SMTP Testing Tool - Advanced Settings");
  });

  test("Advanced SMTP Settings card header is visible", async ({ page }) => {
    const header = page
      .locator(".card-header")
      .filter({ hasText: "Advanced SMTP Settings" });
    await expect(header).toBeVisible();
  });

  test("card header h5 contains 'Advanced SMTP Settings'", async ({ page }) => {
    await expect(page.locator(".card-header h5")).toContainText(
      "Advanced SMTP Settings"
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

  test("SMTP Client Hostname field is present with default value", async ({
    page,
  }) => {
    const field = page.getByLabel("SMTP Client Hostname:");
    await expect(field).toBeVisible();
    await expect(field).toHaveValue("testhost.local");
  });

  test("Default Sender Address field is present", async ({ page }) => {
    const field = page.getByLabel("Default Sender Address:");
    await expect(field).toBeVisible();
    await expect(field).toHaveValue("test@example.com");
  });

  test("Logging Level select has expected options", async ({ page }) => {
    const select = page.getByLabel("Logging Level:");
    await expect(select).toBeVisible();
    await expect(select.locator("option")).toContainText([
      "Debug",
      "Info",
      "Warning",
      "Error",
    ]);
  });

  test("Logging Level default is Warning", async ({ page }) => {
    const select = page.getByLabel("Logging Level:");
    // The option value is stored as "WARNING" (all caps) in the DB
    await expect(select).toHaveValue("WARNING");
  });

  test("Log Retention (days) field is present with default value 7", async ({
    page,
  }) => {
    const field = page.getByLabel("Log Retention (days):");
    await expect(field).toBeVisible();
    await expect(field).toHaveValue("7");
  });

  test("Max Attachment Size (MB) field is present with default value 5", async ({
    page,
  }) => {
    const field = page.getByLabel("Max Attachment Size (MB):");
    await expect(field).toBeVisible();
    await expect(field).toHaveValue("5");
  });

  test("Log SMTP Traffic checkbox is checked by default", async ({ page }) => {
    const cb = page.getByLabel("Log SMTP Traffic");
    await expect(cb).toBeVisible();
    await expect(cb).toBeChecked();
  });

  test("Log Message Content checkbox is checked by default", async ({
    page,
  }) => {
    const cb = page.getByLabel("Log Message Content");
    await expect(cb).toBeVisible();
    await expect(cb).toBeChecked();
  });

  test("Save Settings button is visible with purple gradient", async ({
    page,
  }) => {
    const btn = page.getByRole("button", { name: "Save Settings" });
    await expect(btn).toBeVisible();
    const bg = await btn.evaluate((el) => getComputedStyle(el).backgroundImage);
    expect(bg).toContain("124, 58, 237");
    expect(bg).toContain("59, 130, 246");
  });

  test("Back to SMTP Profiles link navigates to /settings", async ({
    page,
  }) => {
    const link = page.getByRole("link", { name: "Back to SMTP Profiles" });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/settings/);
  });
});

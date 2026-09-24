/**
 * navigation.spec.ts
 *
 * Tests the navbar navigation links present across all pages.
 * Verifies that all main navigation targets resolve and load correctly.
 */
import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("navbar contains Send Email link that navigates to /", async ({
    page,
  }) => {
    await page.goto("/settings");
    await page.getByRole("link", { name: "Send Email" }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page).toHaveTitle("SMTP Testing Tool - Send Email");
  });

  test("navbar contains SMTP Settings link that navigates to /settings", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "SMTP Settings" }).click();
    await expect(page).toHaveURL(/\/settings/);
    await expect(page).toHaveTitle("SMTP Testing Tool - SMTP Settings");
  });

  test("navbar contains Templates link that navigates to /templates", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Templates" }).click();
    await expect(page).toHaveURL(/\/templates/);
    await expect(page).toHaveTitle("SMTP Testing Tool - Email Templates");
  });

  test("navbar contains Logs link that navigates to /logs", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Logs" }).click();
    await expect(page).toHaveURL(/\/logs/);
    await expect(page).toHaveTitle("SMTP Testing Tool - Email Logs");
  });
});

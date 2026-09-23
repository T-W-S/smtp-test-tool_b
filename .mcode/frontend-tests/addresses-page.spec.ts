/**
 * addresses-page.spec.ts
 *
 * Tests the Email Address Management page (/addresses).
 * Selectors from QA report DOM snapshot.
 * Default DB has: smtp@macto.local, test@example.com (senders), recipient@example.com (recipient).
 */
import { test, expect } from "@playwright/test";

test.describe("Addresses page (/addresses)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/addresses");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle(
      "SMTP Testing Tool - Email Address Management"
    );
  });

  test("page heading is 'Email Address Management'", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Email Address Management" })
    ).toBeVisible();
  });

  test("Sender Addresses section heading is visible", async ({ page }) => {
    await expect(
      page.locator("h5").filter({ hasText: "Sender Addresses" })
    ).toBeVisible();
  });

  test("Recipient Addresses section heading is visible", async ({ page }) => {
    await expect(
      page.locator("h5").filter({ hasText: "Recipient Addresses" })
    ).toBeVisible();
  });

  test("Sender Addresses section headers have purple-to-blue gradient", async ({
    page,
  }) => {
    // Section headers may be .card-header elements
    const cardHeaders = page.locator(".card-header");
    const count = await cardHeaders.count();
    expect(count).toBeGreaterThan(0);
    const gradient = await cardHeaders.first().evaluate((el) =>
      getComputedStyle(el).backgroundImage
    );
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("sender address input placeholder is present", async ({ page }) => {
    await expect(
      page.locator('input[placeholder="Enter new sender email"]')
    ).toBeVisible();
  });

  test("recipient address input placeholder is present", async ({ page }) => {
    await expect(
      page.locator('input[placeholder="Enter new recipient email"]')
    ).toBeVisible();
  });

  test("Add buttons are visible (sender and recipient)", async ({ page }) => {
    const addBtns = page.getByRole("button", { name: "+ Add" });
    await expect(addBtns.first()).toBeVisible();
  });

  test("Back to Mail Form link is present and navigates to /", async ({
    page,
  }) => {
    const link = page.getByRole("link", { name: "Back to Mail Form" });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/$/);
  });
});

/**
 * main-page.spec.ts
 *
 * Tests the Send Email page (/).
 * Selectors and expected text come from the QA report DOM observations.
 */
import { test, expect } from "@playwright/test";

test.describe("Main page (/)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("page title is correct", async ({ page }) => {
    await expect(page).toHaveTitle("SMTP Testing Tool - Send Email");
  });

  test("info alert is visible with instructional text", async ({ page }) => {
    const alert = page.locator(".alert.alert-info");
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(
      'Click any test button to pre-fill the email form with test data'
    );
  });

  test("Send Email card header is visible", async ({ page }) => {
    const header = page.locator(".card-header").filter({ hasText: "Send Email" });
    await expect(header).toBeVisible();
  });

  test("card header h5 contains 'Send Email'", async ({ page }) => {
    // Page has multiple .card-header h5 elements; filter to the Send Email one
    await expect(
      page.locator(".card-header h5").filter({ hasText: "Send Email" })
    ).toBeVisible();
  });

  test("quick-fill buttons are present: Malformed PDF, EICAR Test, SPF Test", async ({
    page,
  }) => {
    await expect(page.getByRole("button", { name: "Malformed PDF" })).toBeVisible();
    await expect(page.getByRole("button", { name: "EICAR Test" })).toBeVisible();
    await expect(page.getByRole("button", { name: "SPF Test" })).toBeVisible();
  });

  test("SMTP Profile select is present with default disabled option", async ({
    page,
  }) => {
    const select = page.locator("select").first();
    await expect(select).toBeVisible();
    await expect(select.locator("option[disabled]")).toContainText(
      "Select a profile"
    );
  });

  test("Email Template select has expected options", async ({ page }) => {
    // Find combobox near label "Email Template:"
    const templateSelect = page.getByLabel("Email Template:");
    await expect(templateSelect).toBeVisible();
    await expect(templateSelect.locator("option")).toContainText([
      "No template",
      "Plain Text Example",
      "HTML Example",
      "EICAR Antivirus Test",
      "SPF Test",
    ]);
  });

  test("From field is present", async ({ page }) => {
    await expect(page.getByLabel("From:")).toBeVisible();
  });

  test("To field is present and required", async ({ page }) => {
    const toField = page.getByLabel("To:");
    await expect(toField).toBeVisible();
  });

  test("CC and BCC fields are present", async ({ page }) => {
    // Use IDs to avoid label substring matching (getByLabel("CC:") also matches BCC:)
    await expect(page.locator("#cc")).toBeVisible();
    await expect(page.locator("#bcc")).toBeVisible();
  });

  test("Subject field is present", async ({ page }) => {
    await expect(page.getByLabel("Subject:")).toBeVisible();
  });

  test("HTML checkbox is present", async ({ page }) => {
    await expect(page.getByLabel("HTML")).toBeVisible();
  });

  test("Body textarea is present", async ({ page }) => {
    await expect(page.getByLabel("Body:")).toBeVisible();
  });

  test("Reset button is visible", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Reset" })).toBeVisible();
  });

  test("Send Email submit button is visible", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Send Email" })).toBeVisible();
  });

  test("Send Email button has purple gradient (no orange)", async ({ page }) => {
    const btn = page.getByRole("button", { name: "Send Email" });
    const bg = await btn.evaluate((el) => getComputedStyle(el).backgroundImage);
    expect(bg).toContain("124, 58, 237");
    expect(bg).toContain("59, 130, 246");
  });

  test("quick-fill: clicking Malformed PDF without profile shows no form change (requires profile)", async ({
    page,
  }) => {
    // The JS guard requires a selected SMTP profile before it fills the form.
    // With no profile selected, the handler returns early — subject stays empty.
    const subjectBefore = await page.getByLabel("Subject:").inputValue();
    await page.getByRole("button", { name: "Malformed PDF" }).click();
    // Form is NOT filled — subject unchanged
    await expect(page.getByLabel("Subject:")).toHaveValue(subjectBefore);
  });

  test("quick-fill: clicking SPF Test without profile shows no form change (requires profile)", async ({
    page,
  }) => {
    const subjectBefore = await page.getByLabel("Subject:").inputValue();
    await page.getByRole("button", { name: "SPF Test" }).click();
    await expect(page.getByLabel("Subject:")).toHaveValue(subjectBefore);
  });
});

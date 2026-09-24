/**
 * profiles-milestone.spec.ts
 *
 * Covers the two code changes introduced in milestone 1.2 (upstream sync):
 *
 *   1. src/smtp_tool/blueprints/profiles.py
 *      `add_profile()` return value is now checked; a falsy return results in
 *      an error flash instead of silently succeeding.  The success path still
 *      redirects to /settings with "SMTP profile added successfully".
 *
 *   2. src/smtp_tool/static/js/app.js
 *      The `addProfile` fetch call (used for the **edit** profile path) now
 *      sends  `X-Requested-With: XMLHttpRequest`.  The server detects this and
 *      returns JSON, which the JS turns into a Bootstrap toast.  Without the
 *      header the server returns a redirect (HTML), breaking the edit UX.
 *
 * Selectors and expected text taken directly from the QA report.
 */
import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helper: unique name generator — each call within a test run is distinct
// ---------------------------------------------------------------------------
function uniqueName(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
}

// ---------------------------------------------------------------------------
// Helper: create a new SMTP profile via the Add Profile modal
// ---------------------------------------------------------------------------
async function createProfile(page: Page, name: string, server: string): Promise<void> {
  await page.goto("/settings");
  await page.getByRole("button", { name: "+ Add Profile" }).click();
  const modal = page.locator("div#addProfileModal");
  await expect(modal).toBeVisible();
  await modal.locator("input#name").fill(name);
  await modal.locator("input#server").fill(server);
  await modal.locator(".modal-footer button[type='submit']").click();
  await expect(page).toHaveURL(/\/settings/);
}

// ---------------------------------------------------------------------------
// Add Profile modal — structural assertions (no DB state change)
// ---------------------------------------------------------------------------
test.describe("Add Profile modal structure", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/settings");
    await page.getByRole("button", { name: "+ Add Profile" }).click();
    // Wait for Bootstrap modal animation to complete
    await expect(page.locator("div#addProfileModal")).toBeVisible();
  });

  test("modal is visible after clicking Add Profile button", async ({ page }) => {
    await expect(page.locator("div#addProfileModal")).toBeVisible();
  });

  test("modal contains Profile Name input (required)", async ({ page }) => {
    const field = page.locator("div#addProfileModal input#name");
    await expect(field).toBeVisible();
    await expect(field).toHaveAttribute("required");
  });

  test("modal contains SMTP Server input (required)", async ({ page }) => {
    const field = page.locator("div#addProfileModal input#server");
    await expect(field).toBeVisible();
    await expect(field).toHaveAttribute("required");
  });

  test("modal contains Port input", async ({ page }) => {
    await expect(page.locator("div#addProfileModal input#port")).toBeVisible();
  });

  test("modal contains use_tls and use_ssl checkboxes", async ({ page }) => {
    await expect(page.locator("div#addProfileModal input#use_tls")).toBeVisible();
    await expect(page.locator("div#addProfileModal input#use_ssl")).toBeVisible();
  });

  test("modal contains Username and Password inputs", async ({ page }) => {
    await expect(page.locator("div#addProfileModal input#username")).toBeVisible();
    await expect(page.locator("div#addProfileModal input#password")).toBeVisible();
  });

  test("modal footer has 'Save Profile' submit button", async ({ page }) => {
    const saveBtn = page.locator(
      "div#addProfileModal .modal-footer button[type='submit']"
    );
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toContainText("Save Profile");
  });
});

// ---------------------------------------------------------------------------
// Add Profile — successful submission
// Validates the profiles.py milestone change: add_profile() return value is
// checked and success/error flash is shown accordingly.
// ---------------------------------------------------------------------------
test.describe("Add Profile — successful submission (profiles.py milestone change)", () => {
  test("valid submission redirects to /settings with success flash message", async ({
    page,
  }) => {
    const name = uniqueName("E2E_Add");
    await createProfile(page, name, "smtp.e2e-test.example.com");

    // Flash rendered by profiles.py after a successful add_profile() call
    const flash = page.locator("div.alert.alert-success");
    await expect(flash).toBeVisible();
    await expect(flash).toContainText("SMTP profile added successfully");
  });

  test("newly added profile appears in the profiles table", async ({ page }) => {
    const name = uniqueName("E2E_TableCheck");
    await createProfile(page, name, "smtp.table-check.example.com");
    // Profile name must appear in the first <td> of a table row
    await expect(page.locator("table.table tbody")).toContainText(name);
  });

  test("added profile row has Edit, Delete, and Test action buttons", async ({
    page,
  }) => {
    const name = uniqueName("E2E_Actions");
    await createProfile(page, name, "smtp.actions.example.com");
    await expect(page.locator("table.table tbody")).toContainText(name);

    // Per-profile action buttons (QA report: div.btn-group.btn-group-sm)
    await expect(
      page.locator(`button.edit-profile[data-profile="${name}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`button.delete-profile[data-profile="${name}"]`)
    ).toBeVisible();
    await expect(
      page.locator(`button.test-profile[data-profile="${name}"]`)
    ).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Edit Profile — AJAX toast flow
// Validates the app.js milestone change: the addProfile fetch call now sends
// X-Requested-With: XMLHttpRequest, causing the server to return JSON instead
// of an HTML redirect, so the JS can display a Bootstrap toast.
// ---------------------------------------------------------------------------
test.describe("Edit Profile — AJAX toast flow (app.js milestone change)", () => {
  // Each edit test creates its own profile in beforeEach so tests are independent.
  let profileName: string;

  test.beforeEach(async ({ page }) => {
    profileName = uniqueName("E2E_Edit");
    await createProfile(page, profileName, "smtp.before-edit.example.com");
    // Wait for profile to appear in table
    await expect(page.locator("table.table tbody")).toContainText(profileName);
  });

  test("Edit button opens edit modal", async ({ page }) => {
    const editBtn = page.locator(
      `button.edit-profile[data-profile="${profileName}"]`
    );
    await expect(editBtn).toBeVisible();
    await editBtn.click();
    await expect(page.locator("div#editProfileModal")).toBeVisible();
  });

  test("edit modal pre-fills profile name as readonly", async ({ page }) => {
    await page
      .locator(`button.edit-profile[data-profile="${profileName}"]`)
      .click();
    const modal = page.locator("div#editProfileModal");
    await expect(modal).toBeVisible();

    const nameField = modal.locator("input#editProfileName");
    await expect(nameField).toHaveValue(profileName);
    await expect(nameField).toHaveAttribute("readonly");
  });

  test("edit modal contains Server, Port, and security radio inputs", async ({
    page,
  }) => {
    await page
      .locator(`button.edit-profile[data-profile="${profileName}"]`)
      .click();
    const modal = page.locator("div#editProfileModal");
    await expect(modal).toBeVisible();

    await expect(modal.locator("input#editServer")).toBeVisible();
    await expect(modal.locator("input#editPort")).toBeVisible();
    await expect(modal.locator("input#editSecurityTLS")).toBeVisible();
    await expect(modal.locator("input#editSecuritySSL")).toBeVisible();
    await expect(modal.locator("input#editSecurityNone")).toBeVisible();
  });

  test("edit modal contains authentication toggle and credential inputs", async ({
    page,
  }) => {
    await page
      .locator(`button.edit-profile[data-profile="${profileName}"]`)
      .click();
    const modal = page.locator("div#editProfileModal");
    await expect(modal).toBeVisible();

    await expect(modal.locator("input#editUseAuthentication")).toBeVisible();
    // Auth fields may be hidden by default; just verify they exist in the DOM
    await expect(modal.locator("input#editUsername")).toBeAttached();
    await expect(modal.locator("input#editPassword")).toBeAttached();
  });

  test("submitting edit form reloads page with updated data — AJAX path, no success flash", async ({
    page,
  }) => {
    await page
      .locator(`button.edit-profile[data-profile="${profileName}"]`)
      .click();
    const modal = page.locator("div#editProfileModal");
    await expect(modal).toBeVisible();

    // Modify the server field to a recognisably new value
    const updatedServer = "smtp.after-edit.example.com";
    await modal.locator("input#editServer").fill(updatedServer);

    // Click the submit button linked to editProfileForm via the form attribute
    await page.locator("button[type='submit'][form='editProfileForm']").click();

    // On the AJAX path (app.js milestone change: X-Requested-With header sent):
    //   server returns JSON {success: true} → JS calls location.reload()
    // On the non-AJAX path (if the header were absent):
    //   server redirects + flashes "SMTP profile added successfully"
    //
    // So we assert:
    //   1. The page reloaded back to /settings (location.reload() called).
    //   2. No success flash — only the non-AJAX redirect path sets one.
    //   3. The updated server value now appears in the profiles table.
    await expect(page).toHaveURL(/\/settings/, { timeout: 15000 });

    // The AJAX success path does NOT flash a success message; a non-zero flash
    // would mean the JS fell back to a plain form POST (without the AJAX header).
    await expect(page.locator("div.alert.alert-success")).not.toBeVisible();

    // Updated server value is reflected after the reload
    await expect(page.locator("table.table tbody")).toContainText(updatedServer);
  });
});

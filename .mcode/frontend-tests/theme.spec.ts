/**
 * theme.spec.ts
 *
 * Verifies the purple/blue glossy dark theme (Milestone 1.1).
 * Tests computed CSS styles: body background, card-header gradient,
 * btn-primary gradient, and alert-info glass-morphism colour.
 * All assertions are derived from QA report computed-style observations.
 */
import { test, expect } from "@playwright/test";

test.describe("Theme: global CSS custom properties", () => {
  test("body background is near-black dark base (rgb(15, 17, 33))", async ({
    page,
  }) => {
    await page.goto("/");
    const bg = await page.evaluate(() =>
      getComputedStyle(document.body).backgroundColor
    );
    expect(bg).toBe("rgb(15, 17, 33)");
  });

  test("card-header background is purple-to-blue gradient", async ({
    page,
  }) => {
    await page.goto("/");
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".card-header");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    // Gradient must contain both purple (124, 58, 237) and blue (59, 130, 246)
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("btn-primary background is purple-to-blue gradient (no orange)", async ({
    page,
  }) => {
    await page.goto("/");
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".btn-primary");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    expect(gradient).toContain("124, 58, 237");
    expect(gradient).toContain("59, 130, 246");
  });

  test("alert-info uses semi-transparent purple glass-morphism background", async ({
    page,
  }) => {
    await page.goto("/");
    const bg = await page.evaluate(() => {
      const el = document.querySelector(".alert.alert-info");
      return el ? getComputedStyle(el).backgroundColor : "";
    });
    // rgba(124, 58, 237, 0.15) — purple tint
    expect(bg).toContain("124, 58, 237");
  });

  test("no orange color values remain in computed card-header background", async ({
    page,
  }) => {
    await page.goto("/");
    const gradient = await page.evaluate(() => {
      const el = document.querySelector(".card-header");
      return el ? getComputedStyle(el).backgroundImage : "";
    });
    // Orange is roughly 255,165,0 — ensure it is not present
    expect(gradient).not.toContain("255, 165,");
    expect(gradient).not.toContain("255, 87,");
    expect(gradient).not.toContain("255, 100,");
  });
});

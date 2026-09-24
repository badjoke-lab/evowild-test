import { test, expect } from "@playwright/test";

test("S-only V3 loads six-frame S cycle and advances race", async ({ page }, testInfo) => {
  await page.goto("/race-s-only-v3.html");

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-field", "s-only");
  await expect(stage).toHaveAttribute("data-renderer", "pseudo3d-segments");
  await expect(stage).toHaveAttribute("data-s-run-sheet", "ready", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await page.waitForTimeout(1400);

  const distance = Number(await stage.getAttribute("data-selected-distance"));
  const speed = Number(await stage.getAttribute("data-selected-speed"));
  const frame = Number(await stage.getAttribute("data-s-run-frame"));
  const phase = await stage.getAttribute("data-s-run-phase");

  expect(distance).toBeGreaterThan(0);
  expect(speed).toBeGreaterThan(0);
  expect(frame).toBeGreaterThanOrEqual(0);
  expect(frame).toBeLessThan(6);
  expect(["CONTACT", "PUSH", "LIFT", "FLIGHT", "REACH", "LAND"]).toContain(phase);

  if (testInfo.project.name === "desktop-chromium") {
    await page.screenshot({
      path: "test-results/visuals/s-only-v3-desktop.png",
      fullPage: true
    });
  }
});

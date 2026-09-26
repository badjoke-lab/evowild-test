import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("render S shape-v2 baseline comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(60000);

  await page.goto("/shape-v2-review.html", { waitUntil: "domcontentloaded" });
  await expect(page.locator("body")).toHaveAttribute("data-shape-review", "ready", { timeout: 30000 });

  const baseSize = await page.locator("body").getAttribute("data-base-size");
  const v2Size = await page.locator("body").getAttribute("data-v2-size");
  expect(baseSize).toBeTruthy();
  expect(v2Size).toBeTruthy();
  expect(v2Size).not.toBe(baseSize);

  fs.mkdirSync("test-results/shape-v2", { recursive: true });
  await page.screenshot({ path: "test-results/shape-v2/browser-comparison.png", fullPage: true });
  console.log("SHAPE_V2_BROWSER", JSON.stringify({ baseSize, v2Size }));
});

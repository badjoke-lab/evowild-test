import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S-only Road Lab renders pseudo-3D race and animates", async ({ page }, testInfo) => {
  test.setTimeout(45000);
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(String(err)));

  await page.goto("/evowild-test/race-roadlab.html", { waitUntil: "networkidle" });
  const stage = page.locator(".roadlab");

  await expect(stage).toHaveAttribute("data-state", "ready", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-running", "true", { timeout: 5000 });

  const frames = new Set();
  for (let i = 0; i < 10; i++) {
    frames.add(await stage.getAttribute("data-frame"));
    await page.waitForTimeout(90);
  }
  expect(frames.size).toBeGreaterThanOrEqual(3);
  expect(pageErrors).toEqual([]);

  if (testInfo.project.name === "desktop-chromium") {
    fs.mkdirSync("test-results/visuals", { recursive: true });
    await page.waitForTimeout(2600);
    await page.screenshot({
      path: "test-results/visuals/desktop-roadlab.png",
      fullPage: true
    });
  }
});

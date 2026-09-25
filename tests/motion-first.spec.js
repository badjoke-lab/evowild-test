import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Motion First S runner renders and captures required camera views", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/preview-motion-first/index.html", { waitUntil: "networkidle" });
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#runnerSelect")).toHaveValue("0");

  // Let the S runner reach a readable running pose, then freeze motion.
  await page.waitForTimeout(4200);
  await page.getByRole("button", { name: "PAUSE" }).click();
  await expect(page.locator("#raceState")).toHaveText("PAUSED");

  const views = ["SIDE", "LOW", "CHASE", "FRONT", "PACK"];

  for (const view of views) {
    await page.getByRole("button", { name: view, exact: true }).click();
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${outDir}/motion-first-s-${view.toLowerCase()}.png`,
      fullPage: true
    });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("2.5D race proof loads creature assets and advances", async ({ page }, testInfo) => {
  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/evowild-test/race-2_5d.html", { waitUntil: "networkidle" });

  await expect(page.locator("#race2d")).toBeVisible();
  await expect(page.locator("#stage")).toHaveAttribute("data-assets", "ready", { timeout: 8000 });
  await expect(page.locator("#clock")).not.toHaveText("00:00.00", { timeout: 5000 });
  await expect(page.locator("#rank")).not.toHaveText("— / 18", { timeout: 5000 });

  const canvasInfo = await page.locator("#race2d").evaluate((canvas) => ({
    width: canvas.width,
    height: canvas.height,
    cssWidth: canvas.getBoundingClientRect().width,
    cssHeight: canvas.getBoundingClientRect().height
  }));

  expect(canvasInfo.width).toBeGreaterThan(0);
  expect(canvasInfo.height).toBeGreaterThan(0);
  expect(canvasInfo.cssWidth).toBeGreaterThan(0);
  expect(canvasInfo.cssHeight).toBeGreaterThan(0);
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  await page.locator("#stage").screenshot({
    path: outDir + "/" + testInfo.project.name + "-2_5d-race.png"
  });
});

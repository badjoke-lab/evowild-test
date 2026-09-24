import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("lane 5 pseudo-3D race builds speed and renders without browser errors", async ({ page }, testInfo) => {
  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/evowild-test/race-2_5d-v5.html", { waitUntil: "networkidle" });

  const canvas = page.locator("#race");
  await expect(canvas).toBeVisible();
  await expect(page.locator("#speed")).not.toHaveText("0 km/h", { timeout: 6000 });
  await expect(page.locator("#distance")).not.toHaveText("0m", { timeout: 6000 });

  const info = await canvas.evaluate((el) => ({
    width: el.width,
    height: el.height,
    cssWidth: el.getBoundingClientRect().width,
    cssHeight: el.getBoundingClientRect().height
  }));

  expect(info.width).toBeGreaterThan(0);
  expect(info.height).toBeGreaterThan(0);
  expect(info.cssWidth).toBeGreaterThan(0);
  expect(info.cssHeight).toBeGreaterThan(0);
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  await page.locator(".race-wrap").screenshot({
    path: outDir + "/" + testInfo.project.name + "-lane5-pseudo3d.png"
  });
});

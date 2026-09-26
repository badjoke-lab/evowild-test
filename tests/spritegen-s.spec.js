import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S sprite extraction lane builds an 8-frame transparent side run loop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.stack || String(error)));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/evowild-test/preview-spritegen-s/", { waitUntil: "networkidle" });

  await expect(page.locator("#state")).toHaveText("READY", { timeout: 30000 });
  await expect(page.locator("#source")).toHaveAttribute("data-ready", "1");
  await expect(page.locator("#source")).toHaveAttribute("data-asset", "focus-rigged-v5.glb");
  await expect(page.locator("#source")).toHaveAttribute("data-clip", "EvoWild_S_Run_V5");
  await expect(page.locator("#source")).toHaveAttribute("data-forward-axis", "+Z");
  await expect(page.locator("#source")).toHaveAttribute("data-screen-facing", "right");
  await expect(page.locator("#atlas")).toHaveAttribute("data-frames", "8");
  await expect(page.locator("#atlas")).toHaveAttribute("data-transparent", "1");
  await expect(page.locator("#frameCount")).toHaveText("8 / 8");

  const frame0 = await page.locator("#preview").getAttribute("data-frame");
  await page.waitForTimeout(850);
  const frame1 = await page.locator("#preview").getAttribute("data-frame");
  expect(frame1).not.toBe(frame0);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  await page.locator(".grid").screenshot({
    path: `${outDir}/spritegen-s-side-run-poc.png`
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

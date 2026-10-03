import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Visual Shader Lab V0 renders shader ON/OFF evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/visual-shader-lab.html", { waitUntil: "networkidle" });
  await expect(page.locator("#shader-lab-canvas")).toBeVisible();
  await expect(page.locator("#mode")).toHaveText("SHADER ON");

  await page.waitForTimeout(1600);
  await expect(page.locator("#fps")).not.toHaveText("FPS --");
  await page.screenshot({
    path: `${outDir}/v0-shader-on.png`,
    fullPage: true
  });

  await page.getByRole("button", { name: "Toggle shader" }).click();
  await expect(page.locator("#mode")).toHaveText("SHADER OFF");
  await page.waitForTimeout(900);
  await page.screenshot({
    path: `${outDir}/v0-shader-off.png`,
    fullPage: true
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

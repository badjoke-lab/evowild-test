import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Sakura World lane loads the upstream world, runs S, and captures four views", async ({ page }, testInfo) => {
  test.skip(process.env.SAKURA_WORLD_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(330000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/preview-sakura-world/index.html", { waitUntil: "domcontentloaded" });
  const canvas = page.locator("#view");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-render-lane", "sakura-world", { timeout: 90000 });
  await expect(canvas).toHaveAttribute("data-upstream-world", "de01898e89c7f6ab3fad93fa802f0f5ac66fbd81");
  await expect(canvas).toHaveAttribute("data-head-mass-correction", "removed-v18");
  await expect(canvas).toHaveAttribute("data-head-crest-repair", "skin-weight-v18");
  await expect(canvas).toHaveAttribute("data-head-crest-changed-vertices", /[1-9][0-9]*/);
  await expect(canvas).toHaveAttribute("data-animation-count", /[1-9][0-9]*/);
  await expect(canvas).toHaveAttribute("data-camera-axis-fix", "2");
  await expect(canvas).toHaveAttribute("data-run-direction", "-Z");

  await expect(page.locator("#speed")).toHaveText("5.5 m/s");

  await page.evaluate(() => window.__sakuraWorldLane.pauseRendering());

  for (const [mode, file] of [["threeq", "threeq"], ["chase", "chase"], ["side", "side"], ["front", "front"]]) {
    await page.evaluate((m) => {
      window.__sakuraWorldLane.setRunPosition(13.6);
      window.__sakuraWorldLane.setCameraMode(m);
      window.__sakuraWorldLane.renderOnce();
    }, mode);
    if (mode === "chase") {
      await expect(canvas).toHaveAttribute("data-camera-longitudinal-offset", "4.60");
    } else if (mode === "front") {
      await expect(canvas).toHaveAttribute("data-camera-longitudinal-offset", "-4.80");
    }
    await page.waitForTimeout(120);
    await page.screenshot({ path: `${outDir}/sakura-world-${file}.png`, timeout: 45000 });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});
import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Sakura World lane loads the upstream world, runs S, and captures four views", async ({ page }, testInfo) => {
  test.skip(process.env.SAKURA_WORLD_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

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
  await expect(canvas).toHaveAttribute("data-head-mass-correction", "head-cap-bone-v17");
  await expect(canvas).toHaveAttribute("data-animation-count", /[1-9][0-9]*/);

  await expect.poll(
    () => page.evaluate(() => Number(window.__sakuraWorldLane?.runZ || 0)),
    { timeout: 5000 }
  ).toBeGreaterThan(13.6);

  for (const name of ["3/4", "CHASE", "SIDE", "FRONT"]) {
    await page.getByRole("button", { name, exact: true }).click();
    await page.waitForTimeout(350);
    const file = name === "3/4" ? "threeq" : name.toLowerCase();
    await page.screenshot({ path: `${outDir}/sakura-world-${file}.png`, timeout: 15000 });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});
import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("isolated speed lab loads all run sheets and animates", async ({ page }, testInfo) => {
  test.setTimeout(45000);
  const errors = [];
  page.on("pageerror", (err) => errors.push(String(err)));

  await page.goto("/evowild-test/race-speedlab.html", { waitUntil: "networkidle" });
  const stage = page.locator("#speedlabStage");

  await expect(stage).toHaveAttribute("data-state", "ready", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-motion", "sprite-sheets", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-running", /true|finished/, { timeout: 5000 });

  const observed = { s: new Set(), p: new Set(), e: new Set(), a: new Set() };
  for (let sample = 0; sample < 9; sample++) {
    observed.s.add(await stage.getAttribute("data-frame-s"));
    observed.p.add(await stage.getAttribute("data-frame-p"));
    observed.e.add(await stage.getAttribute("data-frame-e"));
    observed.a.add(await stage.getAttribute("data-frame-a"));
    await page.waitForTimeout(95);
  }

  expect(observed.s.size).toBeGreaterThanOrEqual(3);
  expect(observed.p.size).toBeGreaterThanOrEqual(3);
  expect(observed.e.size).toBeGreaterThanOrEqual(3);
  expect(observed.a.size).toBeGreaterThanOrEqual(3);
  expect(errors).toEqual([]);

  if (testInfo.project.name === "desktop-chromium") {
    fs.mkdirSync("test-results/visuals", { recursive: true });
    await page.waitForTimeout(2600);
    await page.screenshot({ path: "test-results/visuals/desktop-speedlab-chase.png", fullPage: true });
    await page.getByRole("button", { name: "WIDE" }).click();
    await expect(stage).toHaveAttribute("data-camera", "wide");
    await page.waitForTimeout(900);
    await page.screenshot({ path: "test-results/visuals/desktop-speedlab-wide.png", fullPage: true });
  }
});

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

  const before = {
    s: await stage.getAttribute("data-frame-s"),
    p: await stage.getAttribute("data-frame-p"),
    e: await stage.getAttribute("data-frame-e"),
    a: await stage.getAttribute("data-frame-a")
  };

  await page.waitForTimeout(650);

  const after = {
    s: await stage.getAttribute("data-frame-s"),
    p: await stage.getAttribute("data-frame-p"),
    e: await stage.getAttribute("data-frame-e"),
    a: await stage.getAttribute("data-frame-a")
  };

  expect(Object.keys(before).filter((key) => before[key] !== after[key]).length).toBeGreaterThanOrEqual(3);
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

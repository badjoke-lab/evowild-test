import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("2.5D selection capture - Lane 5 V2", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", e => errors.push(e.stack || String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  await page.goto("/evowild-test/race-lane5.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-upstream-runtime", "javascript-racer-common-live");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await expect(stage).toHaveAttribute("data-s-run-sheet", "ready", { timeout: 10000 });

  fs.mkdirSync("artifacts/2p5d-selection", { recursive: true });
  await page.waitForTimeout(1800);
  await stage.screenshot({ path: `artifacts/2p5d-selection/lane5-v2-${testInfo.project.name}-early.png` });
  await page.waitForTimeout(5000);
  await stage.screenshot({ path: `artifacts/2p5d-selection/lane5-v2-${testInfo.project.name}-mid.png` });

  expect(Number(await stage.getAttribute("data-visible-racers"))).toBeGreaterThanOrEqual(3);
  expect(Number(await stage.getAttribute("data-selected-speed"))).toBeGreaterThan(14);
  expect(errors, errors.join("\n")).toEqual([]);
});
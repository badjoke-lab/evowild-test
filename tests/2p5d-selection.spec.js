import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("2.5D selection capture - Four Morph Quality", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", e => errors.push(e.stack || String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  fs.mkdirSync("artifacts/2p5d-selection", { recursive: true });
  await page.waitForTimeout(1800);
  await stage.screenshot({ path: `artifacts/2p5d-selection/four-morph-quality-${testInfo.project.name}-early.png` });
  await page.waitForTimeout(5000);
  await stage.screenshot({ path: `artifacts/2p5d-selection/four-morph-quality-${testInfo.project.name}-mid.png` });

  expect(Number(await stage.getAttribute("data-visible-racers"))).toBeGreaterThanOrEqual(3);
  expect(Number(await stage.getAttribute("data-selected-speed"))).toBeGreaterThan(14);
  expect(errors, errors.join("\n")).toEqual([]);
});
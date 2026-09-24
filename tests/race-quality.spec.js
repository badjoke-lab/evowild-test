import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("four morph race uses all six-frame sheets in fixed-step race", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-engine-lineage", "lane5-fixed-step-plus-four-morph-run-sheets");
  await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
  await expect(stage).toHaveAttribute("data-run-sheets-ready", "4");
  await expect(stage).toHaveAttribute("data-run-sheet-cleanup", "connected-body-alpha");

  await expect(page.locator("#ranking")).toContainText("S01");
  await expect(page.locator("#ranking")).toContainText("P02");
  await expect(page.locator("#ranking")).toContainText("E03");
  await expect(page.locator("#ranking")).toContainText("A04");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 7000 });
  await expect(stage).toHaveAttribute("data-visible-racers", /[1-8]/);
  await expect(stage).toHaveAttribute("data-selected-run-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-selected-run-phase", /(CONTACT|PUSH|LIFT|FLIGHT|REACH|LAND)/);
  await expect(stage).toHaveAttribute("data-s-animated", "true");
  await expect(stage).toHaveAttribute("data-p-animated", "true");
  await expect(stage).toHaveAttribute("data-e-animated", "true");
  await expect(stage).toHaveAttribute("data-a-animated", "true");
  await expect(stage).toHaveAttribute("data-p-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-e-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-a-frame", /[0-5]/);

  await page.waitForTimeout(1800);
  fs.mkdirSync("test-results/visuals", { recursive: true });
  await page.screenshot({
    path: `test-results/visuals/four-morph-quality-${testInfo.project.name}.png`,
    fullPage: true
  });
});
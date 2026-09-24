import { test, expect } from "@playwright/test";

test("four morph race uses all six-frame sheets in fixed-step race", async ({ page }) => {
  await page.goto("/race-quality.html");
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-engine-lineage", "lane5-fixed-step-plus-four-morph-run-sheets");
  await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
  await expect(stage).toHaveAttribute("data-run-sheets-ready", "4");

  await expect(page.locator("#ranking")).toContainText("S01");
  await expect(page.locator("#ranking")).toContainText("P02");
  await expect(page.locator("#ranking")).toContainText("E03");
  await expect(page.locator("#ranking")).toContainText("A04");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 7000 });
  await expect(stage).toHaveAttribute("data-visible-racers", /[1-8]/);
  await expect(stage).toHaveAttribute("data-selected-run-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-selected-run-phase", /(CONTACT|PUSH|LIFT|FLIGHT|REACH|LAND)/);
});
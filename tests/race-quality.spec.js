import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("four morph race uses all six-frame sheets in fixed-step race", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-field-size", "18");
  await expect(stage).toHaveAttribute("data-camera-policy", "selected-plus-nearby");
  await expect(stage).toHaveAttribute("data-engine-lineage", "lane5-fixed-step-plus-four-morph-run-sheets");
  await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
  await expect(stage).toHaveAttribute("data-run-sheets-ready", "4");
  await expect(stage).toHaveAttribute("data-run-sheet-cleanup", "connected-body-alpha");
  await expect(stage).toHaveAttribute("data-visual-depth-stagger", "enabled");
  expect(Number(await stage.getAttribute("data-lane-spread"))).toBeGreaterThan(250);

  await expect(page.locator("#ranking")).toContainText("S01");
  await expect(page.locator("#ranking")).toContainText("P02");
  await expect(page.locator("#ranking")).toContainText("E03");
  await expect(page.locator("#ranking")).toContainText("A04");
  await expect(page.locator("#ranking")).toContainText("P18");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 7000 });
  await expect(stage).toHaveAttribute("data-visible-racers", /\d+/);
  await expect(stage).toHaveAttribute("data-selected-run-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-selected-run-phase", /(CONTACT|PUSH|LIFT|FLIGHT|REACH|LAND)/);
  await expect(stage).toHaveAttribute("data-s-animated", "true");
  await expect(stage).toHaveAttribute("data-p-animated", "true");
  await expect(stage).toHaveAttribute("data-e-animated", "true");
  await expect(stage).toHaveAttribute("data-a-animated", "true");
  await expect(stage).toHaveAttribute("data-p-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-e-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-a-frame", /[0-5]/);
  await expect(stage).toHaveAttribute("data-camera-roll", /-?\d+\.\d+/);
  await expect(stage).toHaveAttribute("data-camera-lift", /-?\d+\.\d+/);
  await expect(stage).toHaveAttribute("data-overtake-pulse", /\d+\.\d+/);

  await page.waitForTimeout(1800);
  fs.mkdirSync("test-results/visuals", { recursive: true });
  await page.screenshot({
    path: `test-results/visuals/four-morph-quality-${testInfo.project.name}.png`,
    fullPage: true
  });
});

test("2.5D Race Agent commands are creature-resolved and morph-dependent", async ({ page }) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  const target = page.locator("#agentTargetSelect");

  await expect(stage).toHaveAttribute("data-field-size", "18");
  await expect(stage).toHaveAttribute("data-agent-model", "command-only-creature-resolved");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await target.selectOption("0");
  await expect(stage).toHaveAttribute("data-agent-target-morph", "S");
  const sStaminaBefore = Number(await stage.getAttribute("data-agent-focus-stamina"));

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(500);
  await expect(stage).toHaveAttribute("data-agent-focus-command", "PUSH");
  const sPushResponse = Number(await stage.getAttribute("data-agent-focus-response"));
  const sFatigue = Number(await stage.getAttribute("data-agent-focus-fatigue"));
  const sStaminaAfter = Number(await stage.getAttribute("data-agent-focus-stamina"));
  expect(sPushResponse).toBeGreaterThan(0.6);
  expect(sFatigue).toBeGreaterThan(0);
  expect(sStaminaAfter).toBeLessThan(sStaminaBefore);

  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await page.waitForTimeout(100);
  await expect(stage).toHaveAttribute("data-agent-focus-command", "NEUTRAL");

  await target.selectOption("2");
  await expect(stage).toHaveAttribute("data-agent-target-morph", "E");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(350);
  const ePushResponse = Number(await stage.getAttribute("data-agent-focus-response"));
  expect(ePushResponse).toBeGreaterThan(0);
  expect(ePushResponse).toBeLessThan(sPushResponse);

  await page.getByRole("button", { name: "CONSERVE", exact: true }).click();
  await page.waitForTimeout(100);
  await expect(stage).toHaveAttribute("data-agent-focus-command", "CONSERVE");
});

test("2.5D race finalizes all 18 runners and exposes classification", async ({ page }, testInfo) => {
  test.setTimeout(30000);
  await page.goto("/evowild-test/race-quality.html?finishReview=1", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-finish-review", "1");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await expect(stage).toHaveAttribute("data-race-state", "finished", { timeout: 18000 });
  await expect(stage).toHaveAttribute("data-result-ready", "1");
  await expect(stage).toHaveAttribute("data-result-count", "18");
  await expect(stage).toHaveAttribute("data-finish-spread-meters", "1.35");
  await expect(stage).toHaveAttribute("data-visual-depth-stagger", "enabled");

  const rows = page.locator("#resultList li");
  await expect(rows).toHaveCount(18);
  await expect(page.locator("#resultsPanel")).toBeVisible();

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-results-${testInfo.project.name}.png`
  });

  const winnerId = await stage.getAttribute("data-winner-id");
  await expect(rows.first()).toHaveAttribute("data-runner-id", winnerId);

  const fieldMinX = Number(await stage.getAttribute("data-field-min-x"));
  const fieldMaxX = Number(await stage.getAttribute("data-field-max-x"));
  expect(fieldMaxX - fieldMinX).toBeGreaterThan(120);

  const times = await rows.evaluateAll((items) =>
    items.map((item) => Number(item.dataset.finishTime))
  );
  expect(times.every(Number.isFinite)).toBe(true);
  for (let i = 1; i < times.length; i++) {
    expect(times[i]).toBeGreaterThanOrEqual(times[i - 1]);
  }
});


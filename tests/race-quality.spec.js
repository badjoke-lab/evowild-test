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

test("2.5D Creature State pressure changes Agent response", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  const target = page.locator("#agentTargetSelect");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await page.waitForTimeout(900);

  let pressured = null;
  for (let index = 0; index < 18; index += 1) {
    await target.selectOption(String(index));
    await page.waitForTimeout(45);
    const state = await stage.evaluate((node) => ({
      pressure: Number(node.dataset.agentFocusPressure),
      stamina: Number(node.dataset.agentFocusStamina),
      fatigue: Number(node.dataset.agentFocusFatigue),
      morph: node.dataset.agentTargetMorph,
      creatureState: node.dataset.agentFocusCreatureState
    }));
    if (Number.isFinite(state.pressure) && state.pressure > 0.10) {
      pressured = { index, ...state };
      break;
    }
  }

  expect(pressured).toBeTruthy();
  expect(["FRESH", "PRESSURED", "WORKING", "TIRED"]).toContain(pressured.creatureState);

  const compatibility = { S: 1.0, P: 0.94, E: 0.76, A: 0.88 }[pressured.morph];
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(220);

  const push = await stage.evaluate((node) => ({
    pressure: Number(node.dataset.agentFocusPressure),
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue),
    response: Number(node.dataset.agentFocusResponse),
    creatureState: node.dataset.agentFocusCreatureState
  }));
  const fatiguePenalty = Math.max(0.25, 1 - push.fatigue * 0.72);
  const noPressureResponse = compatibility * push.stamina * fatiguePenalty;

  expect(push.pressure).toBeGreaterThan(0.08);
  expect(push.response).toBeGreaterThan(0);
  expect(push.response).toBeLessThan(noPressureResponse);
  expect(noPressureResponse - push.response).toBeGreaterThan(0.005);
  expect(["FRESH", "PRESSURED", "WORKING", "TIRED"]).toContain(push.creatureState);
  await expect(page.locator("#agentPressure")).not.toHaveText("");
  await expect(page.locator("#creatureState")).not.toHaveText("");

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-creature-state-${testInfo.project.name}.png`
  });
});

test("2.5D Agent feedback shows command then creature result", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await page.locator("#agentTargetSelect").selectOption("0");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();

  const feedback = page.locator("#agentFeedback");
  await expect(feedback).toBeVisible();
  await expect(page.locator("#agentFeedbackCommand")).toHaveText("PUSH");
  await expect(stage).toHaveAttribute("data-agent-feedback-visible", "1");
  await expect(stage).toHaveAttribute("data-agent-feedback-command", "PUSH");

  await expect
    .poll(async () => page.locator("#agentFeedbackResult").textContent())
    .toMatch(/STRONG|PARTIAL|WEAK/);

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-agent-feedback-${testInfo.project.name}.png`
  });

  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await expect(page.locator("#agentFeedbackCommand")).toHaveText("CLEAR");
  await expect(page.locator("#agentFeedbackResult")).toHaveText("CLEARED");
  await expect(stage).toHaveAttribute("data-agent-feedback-result", "CLEARED");
});

test("2.5D battle readability shows overtake attempt and completion", async ({ page }, testInfo) => {
  test.setTimeout(30000);
  await page.goto("/evowild-test/race-quality.html?battleReview=1", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  const battle = page.locator("#battleReadout");

  await expect(stage).toHaveAttribute("data-battle-review", "1");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await expect.poll(
    async () => stage.getAttribute("data-battle-state"),
    { timeout: 6000 }
  ).toMatch(/OVERTAKE ATTEMPT|CLOSE BATTLE/);

  await expect(stage).toHaveAttribute("data-battle-visible", "1");
  await expect(stage).toHaveAttribute("data-battle-rival-id", "2");
  await expect(battle).toBeVisible();
  await expect(page.locator("#battleMeta")).toContainText("P02");

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-battle-attempt-${testInfo.project.name}.png`
  });

  await expect.poll(
    async () => stage.getAttribute("data-battle-state"),
    { timeout: 12000 }
  ).toBe("OVERTAKE COMPLETE");

  await expect(stage).toHaveAttribute("data-battle-visible", "1");
  await expect(page.locator("#battleState")).toHaveText("OVERTAKE COMPLETE");
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-battle-complete-${testInfo.project.name}.png`
  });
});

test("2.5D traffic sees nearby rivals during fractional lane movement", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html?trafficReview=1", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-traffic-review", "1");
  await expect(stage).toHaveAttribute("data-traffic-model", "continuous-lane-proximity");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await expect.poll(async () => {
    const value = Number(await stage.getAttribute("data-selected-gap-ahead"));
    return Number.isFinite(value) ? value : 999;
  }, { timeout: 3000 }).toBeLessThan(7.5);

  const gap = Number(await stage.getAttribute("data-selected-gap-ahead"));
  expect(gap).toBeGreaterThan(0);
  expect(gap).toBeLessThan(7.5);

  await page.locator("#agentTargetSelect").selectOption("0");
  await page.waitForTimeout(120);
  const pressure = Number(await stage.getAttribute("data-agent-focus-pressure"));
  expect(pressure).toBeGreaterThan(0.08);

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-traffic-proximity-${testInfo.project.name}.png`
  });
});

test("2.5D lane decision chooses real clearance and holds the line", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html?laneReview=1", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-lane-review", "1");
  await expect(stage).toHaveAttribute("data-lane-decision-model", "clearance-score-with-hysteresis");
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await expect.poll(
    async () => Number(await stage.getAttribute("data-selected-lane-decision-count")),
    { timeout: 4000 }
  ).toBe(1);

  await expect(stage).toHaveAttribute("data-selected-target-lane", "0.00");
  const firstTarget = await stage.getAttribute("data-selected-target-lane");
  const firstDecisionCount = Number(await stage.getAttribute("data-selected-lane-decision-count"));

  await page.waitForTimeout(1800);

  expect(await stage.getAttribute("data-selected-target-lane")).toBe(firstTarget);
  expect(Number(await stage.getAttribute("data-selected-lane-decision-count"))).toBe(firstDecisionCount);
  expect(Number(await stage.getAttribute("data-selected-lane-hold-remaining"))).toBeGreaterThan(0);

  const lane = Number(await stage.getAttribute("data-selected-lane"));
  expect(lane).toBeLessThan(0.25);

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-lane-decision-${testInfo.project.name}.png`
  });
});

test("2.5D default start is logically level while visual formation decays", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");

  await expect(stage).toHaveAttribute("data-start-model", "logical-level-visual-grid-decay");
  expect(Number(await stage.getAttribute("data-start-logical-spread"))).toBe(0);
  expect(Number(await stage.getAttribute("data-start-visual-spread"))).toBeGreaterThan(9);

  await expect.poll(async () => {
    const value = Number(await stage.getAttribute("data-start-formation-factor"));
    return Number.isFinite(value) ? value : -1;
  }, { timeout: 3000 }).toBeGreaterThan(0);

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-fair-start-grid-${testInfo.project.name}.png`
  });

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await page.waitForTimeout(2800);

  const formation = Number(await stage.getAttribute("data-start-formation-factor"));
  expect(formation).toBeLessThanOrEqual(0.01);

  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-fair-start-settled-${testInfo.project.name}.png`
  });
});

test("2.5D dense-pack labels avoid overlap and battle HUD clears Agent panel", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html?battleReview=1", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  const battle = page.locator("#battleReadout");
  const agent = page.locator("#agentControl");

  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
  await expect.poll(
    async () => stage.getAttribute("data-battle-visible"),
    { timeout: 6000 }
  ).toBe("1");

  await expect(stage).toHaveAttribute("data-label-layout", "priority-collision-avoidance");
  await expect.poll(
    async () => Number(await stage.getAttribute("data-label-overlap-count")),
    { timeout: 3000 }
  ).toBe(0);

  const visibleLabels = Number(await stage.getAttribute("data-visible-labels"));
  expect(visibleLabels).toBeGreaterThanOrEqual(2);
  expect(visibleLabels).toBeLessThanOrEqual(4);

  const battleBox = await battle.boundingBox();
  const agentBox = await agent.boundingBox();
  expect(battleBox).toBeTruthy();
  expect(agentBox).toBeTruthy();
  const overlaps =
    battleBox.x < agentBox.x + agentBox.width &&
    battleBox.x + battleBox.width > agentBox.x &&
    battleBox.y < agentBox.y + agentBox.height &&
    battleBox.y + battleBox.height > agentBox.y;
  expect(overlaps).toBe(false);

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await stage.screenshot({
    path: `artifacts/2p5d-survivor/2p5d-survivor-pack-readability-${testInfo.project.name}.png`
  });
});

test("2.5D P E A grounded-stride v2 exposes six distinct live phases", async ({ page }, testInfo) => {
  test.setTimeout(45000);

  for (const { id, morph } of [
    { id: 2, morph: "P" },
    { id: 3, morph: "E" },
    { id: 4, morph: "A" }
  ]) {
    await page.goto(`/evowild-test/race-quality.html?motionReview=1&selected=${id}`, { waitUntil: "networkidle" });
    const stage = page.locator("#stage");

    await expect(stage).toHaveAttribute("data-motion-review", "1");
    await expect(stage).toHaveAttribute("data-review-selected-id", String(id));
    await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
    await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });
    await expect(stage).toHaveAttribute("data-selected-morph", morph);
    await expect(stage).toHaveAttribute(`data-${morph.toLowerCase()}-motion-profile`, "grounded-stride-v2");
    await expect(stage).toHaveAttribute(`data-${morph.toLowerCase()}-ground-anchor`, "auto-foot-v2");
    await expect(stage).toHaveAttribute("data-pea-motion-version", "grounded-stride-v2");

    const rawFootSpread = Number(await stage.getAttribute(`data-${morph.toLowerCase()}-foot-spread-raw`));
    expect(Number.isFinite(rawFootSpread)).toBe(true);
    expect(rawFootSpread).toBeGreaterThanOrEqual(0);

    const observed = new Set();
    const captured = new Set();
    fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });

    for (let sample = 0; sample < 40 && observed.size < 6; sample += 1) {
      await page.waitForTimeout(45);
      const frame = Number(await stage.getAttribute("data-selected-run-frame"));
      const phase = await stage.getAttribute("data-selected-run-phase");
      if (Number.isFinite(frame) && frame >= 0 && frame <= 5) {
        observed.add(frame);
        if ([0, 3, 4].includes(frame) && !captured.has(frame)) {
          captured.add(frame);
          await stage.screenshot({
            path: `artifacts/2p5d-survivor/pea-v2-${morph.toLowerCase()}-frame-${frame}-${testInfo.project.name}.png`
          });
        }
      }
      expect(phase).toMatch(/CONTACT|PUSH|LIFT|FLIGHT|REACH|LAND/);
    }

    expect([...observed].sort()).toEqual([0,1,2,3,4,5]);
    expect(Number(await stage.getAttribute(`data-${morph.toLowerCase()}-foot-adjust`))).toBeGreaterThan(-50);
    expect(Number(await stage.getAttribute(`data-${morph.toLowerCase()}-foot-adjust`))).toBeLessThan(50);
  }
});


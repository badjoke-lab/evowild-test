import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("race scene renders and advances", async ({ page }) => {
  test.setTimeout(45000);
  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);

  const state = {
    clock: await page.locator("#clock").textContent(),
    position: await page.locator("#position").textContent(),
    pauseLabel: await page.locator("#pause").textContent(),
    pageErrors,
    consoleErrors
  };
  console.log("RUNTIME_STATE", JSON.stringify(state));

  await expect(page.locator("#game")).toBeVisible();
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "running", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-hud-telemetry", "active", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-visual", "enabled", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-toast", "enabled", { timeout: 6500 });
  await expect(page.locator("#agentPanel")).toBeVisible();
  await expect(page.locator("#agentOrder")).not.toHaveText("");
  await expect(page.locator("#creatureResponse")).toHaveText(/READY|SUCCESS|PARTIAL|FAILED|FINISHED/, { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-orb-count", "18");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-identity", "AG-001", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-profile", "BALANCED", { timeout: 6500 });
  await expect(page.locator("#agentIdentity")).toContainText("AG-001");
  await expect(page.locator("#agentProfile")).toHaveText("BALANCED");
  await expect(page.locator("#agentCompatibility")).toHaveText("100%");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-compatibility", "100");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-policy", "4.2|18|1.040|900");
  await expect(page.locator("#agentPolicyRule")).toContainText("PASS 4.2m");
  await expect(page.locator("#agentRecord")).toHaveText("NO STARTS");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-starts", "0");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-pending-profile", "");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-version-history", "1");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-log-events", /[1-9]\d*/, { timeout: 6500 });
  await expect(page.locator("#agentLog .agent-log-row").first()).toBeVisible();
  await expect(page.locator("#creatureStateCard")).toBeVisible();
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-state", "active", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-condition", /FRESH|WORKING|TIRING|STRAINED|FINISHED/, { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-traffic", /CLEAR|NEAR|TIGHT|BLOCKED/, { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-execution", /READY|SUCCESS|PARTIAL|FAILED|FINISHED/, { timeout: 6500 });
  await expect(page.locator("#stateOutput")).toContainText("%");
  await expect(page.locator("#stateExecution")).not.toHaveText("");
  await expect(page.locator("#fatigue")).toContainText("%");
  await expect(page.locator("#agentFatigue")).toContainText("%");
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-fatigue", /\d+/);
  await expect(page.locator("#stage")).toHaveAttribute("data-directional-sprite-facing", "enabled", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-racers", "4", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-racers", "5", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-four-morph-motion", "ready", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-racers", "4", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-racer", "2", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-motion", "6phase-rig-v3", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-section", /START|MID|BUILD|FINAL/, { timeout: 6500 });
  await expect(page.locator("#remaining")).toContainText("m to go", { timeout: 6500 });
  await expect(page.locator("#leaderGap")).not.toHaveText("", { timeout: 6500 });
  await expect(page.locator("#clock")).not.toHaveText("00:00.00", { timeout: 5000 });

  await page.locator('[data-racer-id="2"]').click();
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "2");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-selected-id", "2");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-identity", "AG-002");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-profile", "PRESSURE");
  await expect(page.locator("#agentIdentity")).toContainText("AG-002");
  await expect(page.locator("#agentProfile")).toHaveText("PRESSURE");
  await expect(page.locator("#agentCompatibility")).toHaveText("102%");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-compatibility", "102");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-policy", "5.4|14|1.060|720");
  await expect(page.locator("#agentPolicyRule")).toContainText("PASS 5.4m");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-log-events", /[1-9]\d*/, { timeout: 3000 });
  await expect(page.locator("#selectedName")).toContainText("#02 Brim");
  await expect(page.locator("#selectedTitle")).toHaveText("Selected #02");
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-motion", "6phase-rig-v3");
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-motion-phase", /CONTACT|PUSH|LIFT|FLIGHT|REACH|LAND/, { timeout: 3000 });
  await expect(page.locator("#stateOutput")).toContainText("%");
  await expect(page.locator("#stateLane")).not.toHaveText("");
  await expect(page.locator("#position")).not.toHaveText("— / 18", { timeout: 5000 });
  await expect(page.locator(".runtime-status")).toBeHidden({ timeout: 5000 });

  const canvasInfo = await page.locator("#game").evaluate((canvas) => ({
    width: canvas.width,
    height: canvas.height,
    cssWidth: canvas.getBoundingClientRect().width,
    cssHeight: canvas.getBoundingClientRect().height
  }));

  expect(canvasInfo.width).toBeGreaterThan(0);
  expect(canvasInfo.height).toBeGreaterThan(0);
  expect(canvasInfo.cssWidth).toBeGreaterThan(0);
  expect(canvasInfo.cssHeight).toBeGreaterThan(0);
});


test("capture mobile race camera views", async ({ page }, testInfo) => {
  test.setTimeout(70000);
  test.skip(testInfo.project.name !== "android-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  await page.getByRole("button", { name: "1 Morph" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
  await expect(page.locator("#stage")).toHaveAttribute("data-s-asset", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-concept-morphs", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-race2p5d", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-speed-fx", "dynamic", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-edge-rhythm", "curb-v1", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-rhythm-objects", "dense-v2", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-quality-pass", "floor-v2", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-cycle", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-frames", "6", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-sheet", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-source", "sprite-sheet", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-animated-racers", "5", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-follow-occlusion-fade", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-presentation", "v12", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-hud-telemetry", "active", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-visual", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-toast", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-orb-count", "18", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-fatigue", /\d+/, { timeout: 8000 });
  await expect(page.locator("#agentFatigue")).toContainText("%");
  await expect(page.locator("#agentPanel")).toBeHidden();
  for (const morph of ["S", "P", "E", "A"]) {
    await page.locator(`[data-morph="${morph}"]`).click();
    await page.waitForTimeout(350);
    await page.locator("#stage").screenshot({ path: `${outDir}/android-morph-${morph}.png` });
  }

  const views = [
    ["race", "2 Race", "RACE VIEW"],
    ["follow", "3 Follow", "FOLLOW VIEW"],
    ["tactical", "4 Tactical", "TACTICAL VIEW"]
  ];

  for (const [name, buttonText, label] of views) {
    await page.getByRole("button", { name: buttonText }).click();
    await expect(page.locator("#viewLabel")).toHaveText(label);
    if (name === "race") {
      await expect(page.locator("#stage")).toHaveAttribute("data-race-camera", "wide-pack", { timeout: 8000 });
      await expect(page.locator("#agentPanel")).toBeVisible();
    }
    await page.waitForTimeout(900);
    await page.locator("#stage").screenshot({ path: `${outDir}/android-${name}.png` });
  }

  await page.getByRole("button", { name: "3 Follow" }).click();
  const observedFrames = new Set();
  const observedPhases = new Set();
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(110);
    observedFrames.add(await page.locator("#stage").getAttribute("data-s-run-frame"));
    observedPhases.add(await page.locator("#stage").getAttribute("data-s-run-phase"));
  }
  expect(observedFrames.size).toBeGreaterThanOrEqual(4);
  expect(observedPhases.size).toBeGreaterThanOrEqual(4);
  await page.locator("#stage").screenshot({ path: `${outDir}/android-s-run-proof.png` });
});


test("record 2.5D race speed proof", async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?proof=s-run", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race2p5d", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-cycle", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-frames", "6", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-sheet", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-source", "sprite-sheet", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-animated-racers", "5", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-follow-occlusion-fade", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-presentation", "v12", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-hud-telemetry", "active", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-proof", "isolated", { timeout: 8000 });
  await page.getByRole("button", { name: "3 Follow" }).click();
  await page.waitForTimeout(7200);
  const video = page.video();
  await page.close();
  const raw = await video.path();
  const finalPath = `${outDir}/desktop-2p5d-animated-s-proof.webm`;
  fs.renameSync(raw, finalPath);
  await context.close();
});


test("record cinematic race presentation", async ({ browser }, testInfo) => {
  test.setTimeout(50000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?presentation=1", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-presentation-mode", "cinematic", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-presentation-field", "s-only-5", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "17", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-presentation", "v12", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-four-morph-motion", "ready", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  await page.waitForTimeout(4200);
  await page.screenshot({ path: `${outDir}/desktop-cinematic-race.png`, fullPage: true });
  await page.waitForTimeout(4200);
  await page.screenshot({ path: `${outDir}/desktop-cinematic-race-late.png`, fullPage: true });

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/desktop-cinematic-race.webm`);
  await context.close();
});


test("record full field and non-S follow motion proof", async ({ browser }, testInfo) => {
  test.setTimeout(45000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "running", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-racers", "4", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-racers", "5", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-four-morph-motion", "ready", { timeout: 6500 });
  await page.getByRole("button", { name: "2 Race" }).click();
  await page.waitForTimeout(3200);

  await page.locator('[data-racer-id="2"]').click();
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "2");
  await expect(page.locator("#stage")).toHaveAttribute("data-creature-state", "active", { timeout: 3000 });
  await page.getByRole("button", { name: "3 Follow" }).click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${outDir}/desktop-agent-creature-state.png`, fullPage: true });
  await page.waitForTimeout(2700);

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/desktop-2p5d-field-motion.webm`);
  await context.close();
});


test("record isolated original-sprite P cutout rig", async ({ browser }, testInfo) => {
  test.setTimeout(45000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?proof=p-rig", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-proof", "isolated", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "2");
  await expect(page.locator("#stage")).toHaveAttribute("data-p-cutout-motion", "6phase-rig-v3", { timeout: 6500 });
  await page.waitForTimeout(6200);
  await page.locator("#stage").screenshot({ path: `${outDir}/desktop-p-cutout-proof.png` });

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/desktop-p-cutout-proof.webm`);
  await context.close();
});


test("record isolated original-sprite E cutout rig", async ({ browser }, testInfo) => {
  test.setTimeout(45000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?proof=e-rig", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-proof", "isolated", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-racers", "4");
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-racer", "3");
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "3");
  await expect(page.locator("#stage")).toHaveAttribute("data-e-cutout-motion", "6phase-rig-v1", { timeout: 6500 });

  const observed = new Set();
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(120);
    observed.add(await page.locator("#stage").getAttribute("data-selected-motion-phase"));
  }
  expect(observed.size).toBeGreaterThanOrEqual(4);

  await page.waitForTimeout(4500);
  await page.locator("#stage").screenshot({ path: `${outDir}/desktop-e-cutout-proof.png` });

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/desktop-e-cutout-proof.webm`);
  await context.close();
});


test("record isolated original-sprite A cutout rig", async ({ browser }, testInfo) => {
  test.setTimeout(45000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?proof=a-rig", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-rig", "loaded", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-proof", "isolated", { timeout: 6500 });
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-racers", "5");
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-racer", "4");
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "4");
  await expect(page.locator("#stage")).toHaveAttribute("data-a-cutout-motion", "6phase-rig-v1", { timeout: 6500 });

  const observed = new Set();
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(120);
    observed.add(await page.locator("#stage").getAttribute("data-selected-motion-phase"));
  }
  expect(observed.size).toBeGreaterThanOrEqual(4);

  await page.waitForTimeout(4500);
  await page.locator("#stage").screenshot({ path: `${outDir}/desktop-a-cutout-proof.png` });

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/desktop-a-cutout-proof.webm`);
  await context.close();
});

test("race reaches results and rematch returns to countdown", async ({ page }, testInfo) => {
  test.setTimeout(30000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  await page.goto("/evowild-test/?proof=finish", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-distance", "45");
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "finished", { timeout: 18000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-finish-count", "18");
  await expect(page.locator("#resultsPanel")).toBeVisible();
  await expect(page.locator("#resultsList .result-row")).toHaveCount(18);
  await expect(page.locator("#resultsList .result-agent")).toHaveCount(18);
  await expect(page.locator("#resultsList .result-agent").first()).toContainText("AG-");
  await expect(page.locator("#resultHeadline")).toContainText("Aster");
  await expect(page.locator("#stage")).toHaveAttribute("data-result-agent-summary", "ready");
  await expect(page.locator("#stage")).toHaveAttribute("data-result-agent-decisions", /[1-9]\d*/);
  await expect(page.locator("#resultAgentIdentity")).toContainText("AG-001");
  await expect(page.locator("#resultAgentPolicy")).toContainText("COMPAT");
  await expect(page.locator("#stage")).toHaveAttribute("data-result-agent-compatibility", /\d+/);
  await expect(page.locator("#resultDecisions")).not.toHaveText("0");
  await expect(page.locator("#resultCompatibility")).toContainText("%");
  await expect(page.locator("#stage")).toHaveAttribute("data-result-agent-compatibility", /\d+/, { timeout: 3000 });
  await expect(page.locator("#resultFinalFatigue")).toContainText("%");
  await expect(page.locator("#resultAgentRecord")).toContainText("Race history 1");
  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  await page.screenshot({ path: `${outDir}/desktop-agent-result-summary.png`, fullPage: true });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-starts", "1", { timeout: 3000 });
  await expect(page.locator("#agentRecord")).toContainText("1S");

  await page.locator('[data-result-racer-id="2"]').click();
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "2");
  await expect(page.locator("#resultHeadline")).toContainText("Brim");
  await expect(page.locator("#resultAgentIdentity")).toContainText("AG-002");
  await expect(page.locator('[data-result-racer-id="2"]')).toHaveClass(/selected/);

  await page.locator('[data-result-racer-id="1"]').click();
  await expect(page.locator("#stage")).toHaveAttribute("data-selected-racer", "1");
  await expect(page.locator("#resultAgentIdentity")).toContainText("AG-001");

  await page.locator('#agentSetupCard [data-agent-policy="PRESSURE"]').click();
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-pending-profile", "PRESSURE");
  await expect(page.locator("#agentSetupStatus")).toContainText("NEXT PRESSURE");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-version-history", "1");

  await page.getByRole("button", { name: "Rematch" }).click();
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "countdown");
  await expect(page.locator("#resultsPanel")).toBeHidden();
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-starts", "1");
  await expect(page.locator("#agentRecord")).toContainText("1S");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-profile", "PRESSURE", { timeout: 3000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-version", "v2", { timeout: 3000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-pending-profile", "");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-version-history", "2");
  await expect(page.locator("#agentProfile")).toHaveText("PRESSURE");
  await expect(page.locator("#agentCompatibility")).toHaveText("103%");
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-compatibility", "103");
  await expect(page.locator("#agentIdentity")).toContainText("/ v2");
});

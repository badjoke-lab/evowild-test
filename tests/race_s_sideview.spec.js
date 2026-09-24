import { test, expect } from "@playwright/test";
import fs from "node:fs";

async function waitForPhase(page, phase, timeout = 3000) {
  return page.evaluate(({ phase, timeout }) => new Promise((resolve, reject) => {
    const stage = document.querySelector("#stage");
    const started = performance.now();
    const tick = () => {
      if (stage?.dataset.motionPhase === phase) return resolve(true);
      if (performance.now() - started > timeout) return reject(new Error("phase timeout: " + phase));
      requestAnimationFrame(tick);
    };
    tick();
  }), { phase, timeout });
}

test("S visual lane stays one complete creature and covers a grounded six-phase gait", async ({ page }, testInfo) => {
  test.setTimeout(60000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", error => pageErrors.push(error.stack || String(error)));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/evowild-test/race-s-sideview.html", { waitUntil: "networkidle" });

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-mode", "s-solo-motion");
  await expect(stage).toHaveAttribute("data-creature-count", "1");
  await expect(stage).toHaveAttribute("data-agent", "off");
  await expect(stage).toHaveAttribute("data-hud", "off");
  await expect(stage).toHaveAttribute("data-race-logic", "off");
  await expect(stage).toHaveAttribute("data-rig-ready", "true", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-frame-source", "s-run-sheet");
  await expect(page.locator(".hud")).toHaveCount(0);
  await expect(page.locator("#motionCanvas")).toBeVisible();

  const samples = await page.evaluate(async () => {
    const stage = document.querySelector("#stage");
    const out = [];
    for (let i = 0; i < 38; i++) {
      out.push({
        phase: stage.dataset.motionPhase,
        lift: Number(stage.dataset.visualLift || 0),
        ground: Number(stage.dataset.groundAnchorY || 0),
        bottom: Number(stage.dataset.spriteBottomY || 0),
        pitch: Number(stage.dataset.bodyPitch || 0),
        frame: Number(stage.dataset.frameIndex || 0)
      });
      await new Promise(resolve => setTimeout(resolve, 24));
    }
    return out;
  });

  const phases = new Set(samples.map(sample => sample.phase));
  for (const phase of ["CONTACT", "PUSH", "RECOVERY", "FLIGHT", "REACH", "LAND"]) {
    expect(phases.has(phase), "missing motion phase: " + phase).toBeTruthy();
  }

  const contact = samples.filter(sample => sample.phase === "CONTACT");
  expect(contact.length).toBeGreaterThan(0);
  expect(Math.max(...contact.map(sample => Math.abs(sample.bottom - sample.ground)))).toBeLessThanOrEqual(1);

  const flight = samples.filter(sample => sample.phase === "FLIGHT");
  expect(flight.length).toBeGreaterThan(0);
  expect(Math.max(...flight.map(sample => sample.lift))).toBeGreaterThan(20);

  expect(new Set(samples.map(sample => sample.frame)).size).toBe(6);
  const pitches = samples.map(sample => sample.pitch);
  expect(Math.max(...pitches) - Math.min(...pitches)).toBeGreaterThan(3);

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals", { recursive: true });

  const expectedCells = {
    CONTACT: "1,1",
    PUSH: "1,0",
    RECOVERY: "0,1",
    FLIGHT: "2,0",
    REACH: "0,0",
    LAND: "2,1"
  };

  const capturePhases = testInfo.project.name === "desktop-chromium"
    ? ["CONTACT", "PUSH", "RECOVERY", "FLIGHT", "REACH", "LAND"]
    : ["CONTACT"];

  for (const phase of capturePhases) {
    await page.goto("/evowild-test/race-s-sideview.html?pose=" + phase, { waitUntil: "networkidle" });
    const fixedStage = page.locator("#stage");
    await expect(fixedStage).toHaveAttribute("data-rig-ready", "true", { timeout: 10000 });
    await expect(fixedStage).toHaveAttribute("data-motion-phase", phase);
    await expect(fixedStage).toHaveAttribute("data-pose-cell", expectedCells[phase]);
    await fixedStage.screenshot({
      path: "test-results/visuals/" + testInfo.project.name + "-s-motion-" + phase.toLowerCase() + ".png"
    });
  }
});

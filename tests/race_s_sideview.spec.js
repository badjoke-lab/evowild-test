import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S visual lane is one articulated creature with grounded gait phases", async ({ page }, testInfo) => {
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
  await expect(page.locator(".hud")).toHaveCount(0);
  await expect(page.locator("#motionCanvas")).toBeVisible();

  const samples = await page.evaluate(async () => {
    const stage = document.querySelector("#stage");
    const out = [];
    for (let i = 0; i < 34; i++) {
      out.push({
        phase: stage.dataset.motionPhase,
        contacts: Number(stage.dataset.contactCount || 0),
        contactError: Number(stage.dataset.contactError || 0),
        bodyY: Number(stage.dataset.bodyY || 0),
        pitch: Number(stage.dataset.bodyPitch || 0),
        flight: stage.dataset.flight
      });
      await new Promise(resolve => setTimeout(resolve, 25));
    }
    return out;
  });

  const phases = new Set(samples.map(sample => sample.phase));
  for (const phase of ["CONTACT", "PUSH", "RECOVERY", "FLIGHT", "REACH", "LAND"]) {
    expect(phases.has(phase), `missing motion phase: ${phase}`).toBeTruthy();
  }

  const contactSamples = samples.filter(sample => sample.contacts > 0);
  expect(contactSamples.length).toBeGreaterThan(0);
  expect(Math.max(...contactSamples.map(sample => sample.contactError))).toBeLessThanOrEqual(0.5);
  expect(samples.some(sample => sample.flight === "true")).toBeTruthy();

  const bodyYs = samples.map(sample => sample.bodyY);
  const pitches = samples.map(sample => sample.pitch);
  expect(Math.max(...bodyYs) - Math.min(...bodyYs)).toBeGreaterThan(12);
  expect(Math.max(...pitches) - Math.min(...pitches)).toBeGreaterThan(4);

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals", { recursive: true });

  await expect.poll(
    async () => stage.getAttribute("data-motion-phase"),
    { timeout: 3000, intervals: [20, 30, 40] }
  ).toBe("FLIGHT");

  await stage.screenshot({
    path: `test-results/visuals/${testInfo.project.name}-s-motion-flight.png`
  });
});

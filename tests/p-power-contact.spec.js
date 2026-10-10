import { test, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

// P-only product gate. Uses the Game Studio probe of the actual instanced
// foot and toe vertices; does not trust the solver's maxStanceSlip counter.
const base = "/evowild-test/preview-motion-first-race/index.html?skipStart=1";

function percentile(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor((sorted.length - 1) * p)];
}

test("P proxy real sole/stance contact is measurable in the 18-runner race", async ({ page }, info) => {
  test.setTimeout(90000);
  const probe = await fs.readFile("scripts/gamestudio-3d/probe.js", "utf8");
  await page.route("**/preview-motion-first/main.js", async (route) => {
    const response = await route.fetch();
    await route.fulfill({ response, body: (await response.text()) + "\n" + probe });
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base);
  await expect(page.locator("#scene")).toHaveAttribute("data-runner-count", "18");
  await expect(page.locator("#loading")).toBeHidden();
  await page.selectOption("#runnerSelect", "1"); // P (runner index 1)

  const samples = [];
  const contacts = new Map();
  const stanceY = [];
  let maxDriftZ = 0;
  let worstPenetration = 0;
  let stanceFeet = 0;
  const until = Date.now() + 6500;
  while (Date.now() < until) {
    const snapshot = await page.evaluate(() => window.__gameStudioProbe());
    for (const foot of snapshot.feet) {
      if (foot.morph !== "P" || !foot.stance) continue;
      stanceFeet += 1;
      const key = [foot.id, foot.leg, foot.cycle].join(":");
      if (!contacts.has(key)) contacts.set(key, foot.z);
      const drift = Math.abs(foot.z - contacts.get(key));
      maxDriftZ = Math.max(maxDriftZ, drift);
      worstPenetration = Math.max(worstPenetration, -foot.soleWorldY);
      stanceY.push(foot.soleWorldY);
    }
    samples.push({ frameTime: snapshot.time, raceTime: snapshot.raceTime });
    await page.waitForTimeout(70);
  }
  await page.locator('[data-camera="SIDE"]').click();
  const dir = path.join("artifacts/p-contact-20261011", info.project.name);
  await fs.mkdir(dir, { recursive: true });
  await page.screenshot({ path: path.join(dir, "p-race-side.png") });
  await page.locator('[data-camera="LOW"]').click();
  await page.screenshot({ path: path.join(dir, "p-race-low.png") });
  const summary = {
    project: info.project.name,
    sampleFrames: samples.length,
    stanceFeet,
    stanceContactGroups: contacts.size,
    medianSoleWorldY: stanceY.length ? percentile(stanceY, 0.5) : null,
    minSoleWorldY: stanceY.length ? Math.min(...stanceY) : null,
    maxWorldFootCenterDriftZ: maxDriftZ,
    worstPenetration,
    note: "Observed rendered geometry at emulator/browser cadence, not a physics-friction measure. Qualifying thresholds are provisional; do not call product gate KEEP from this test alone.",
  };
  await fs.writeFile(path.join(dir, "summary.json"), JSON.stringify(summary, null, 2));
  console.log("P_RENDERED_CONTACT", JSON.stringify(summary));
  expect(errors).toEqual([]);
  expect(stanceFeet).toBeGreaterThan(20);
  expect(contacts.size).toBeGreaterThan(5);
  // These are deliberately stricter than the original audit's P sample,
  // but the time sampling differs: use this as a regression gate, not an
  // assertion of an apples-to-apples performance improvement.
  expect(summary.medianSoleWorldY).toBeGreaterThan(-0.10);
  expect(summary.minSoleWorldY).toBeGreaterThan(-0.42);
  expect(maxDriftZ).toBeLessThan(0.27);
});

import { test, expect } from "@playwright/test";
import fs from "node:fs";

const outDir = "artifacts/kimodo-ardy/accel-launch-ab";

async function captureAt(page, candidate, freezeTime) {
  const query = new URLSearchParams({
    skipStart: "1",
    proxyReviewRunner: "0",
    kimodoLaunch: candidate ? "1" : "0",
    kimodoLaunchSource: "accel",
    kimodoLaunchBlend: "0.55",
    kimodoLaunchFreeze: String(freezeTime)
  });
  await page.goto(
    `/evowild-test/preview-motion-first-race/index.html?${query}`,
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#scene")).toBeVisible();
  await page.locator("#runnerSelect").selectOption("0");
  await page.getByRole("button", { name: "SIDE", exact: true }).click({ force: true });
  await page.waitForFunction(() =>
    document.querySelector("#scene")?.dataset.kimodoLaunchFrozen === "1"
  );
  await page.waitForTimeout(180);

  const scene = page.locator("#scene");
  const metrics = await scene.evaluate((el) => ({
    mode: el.dataset.kimodoLaunchMode,
    source: el.dataset.kimodoLaunchSource,
    physics: el.dataset.kimodoLaunchPhysics,
    raceTime: Number(el.dataset.kimodoLaunchRaceTime),
    envelope: Number(el.dataset.kimodoLaunchEnvelope),
    rawLead: Number(el.dataset.kimodoLaunchRawLead),
    appliedLead: Number(el.dataset.kimodoLaunchAppliedLead),
    physicalSpeedRatio: Number(el.dataset.kimodoLaunchPhysicalSpeedRatio),
    bodyPitch: Number(el.dataset.kimodoLaunchBodyPitch),
    pitchBias: Number(el.dataset.kimodoLaunchPitchBias),
    maxStanceSlip: Number(el.dataset.kimodoLaunchMaxStanceSlip)
  }));

  fs.mkdirSync(outDir, { recursive: true });
  const tag = freezeTime.toFixed(1).replace(".", "_");
  await scene.screenshot({
    path: `${outDir}/t${tag}-${candidate ? "accel-candidate" : "baseline"}-side.png`
  });
  return metrics;
}

test("explicit Kimodo acceleration envelope is physics-neutral for S", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_ACCEL_AB_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  const evidence = {};

  for (const t of [2.1, 2.7]) {
    const baseline = await captureAt(page, false, t);
    const candidate = await captureAt(page, true, t);
    evidence[t.toFixed(1)] = { baseline, candidate };

    expect(baseline.source).toBe("accel");
    expect(candidate.source).toBe("accel");
    expect(baseline.physics).toBe("unchanged");
    expect(candidate.physics).toBe("unchanged");
    expect(baseline.raceTime).toBeCloseTo(candidate.raceTime, 6);
    expect(baseline.physicalSpeedRatio).toBeCloseTo(candidate.physicalSpeedRatio, 6);
    expect(baseline.appliedLead).toBe(0);
  }

  expect(evidence["2.1"].candidate.appliedLead).toBeLessThan(0.01);
  expect(evidence["2.7"].candidate.appliedLead).toBeGreaterThan(0.05);
  expect(evidence["2.7"].candidate.pitchBias).toBeLessThan(-0.002);
  expect(Number.isFinite(evidence["2.7"].candidate.maxStanceSlip)).toBeTruthy();

  fs.writeFileSync(
    `${outDir}/metrics.json`,
    JSON.stringify(evidence, null, 2) + "\n"
  );
  await context.close();
});

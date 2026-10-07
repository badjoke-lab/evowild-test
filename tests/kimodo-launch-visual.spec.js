import { test, expect } from "@playwright/test";
import fs from "node:fs";

const outDir = "artifacts/kimodo-ardy/launch-ab";

async function captureLaunch(page, candidate) {
  const query = new URLSearchParams({
    skipStart: "1",
    kimodoLaunch: candidate ? "1" : "0",
    kimodoLaunchBlend: "0.55",
    kimodoLaunchFreeze: "2.1",
    proxyReviewRunner: "0"
  });
  await page.goto(
    `/evowild-test/preview-motion-first-race/index.html?${query.toString()}`,
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#scene")).toBeVisible();
  await page.locator("#runnerSelect").selectOption("0");
  await page.getByRole("button", { name: "SIDE", exact: true }).click({ force: true });

  await page.waitForFunction(() => {
    const scene = document.querySelector("#scene");
    return scene?.dataset.kimodoLaunchFrozen === "1";
  });
  await page.waitForTimeout(250);

  const scene = page.locator("#scene");
  const metrics = await scene.evaluate((el) => ({
    mode: el.dataset.kimodoLaunchMode,
    physics: el.dataset.kimodoLaunchPhysics,
    raceTime: Number(el.dataset.kimodoLaunchRaceTime),
    envelope: Number(el.dataset.kimodoLaunchEnvelope),
    rawLead: Number(el.dataset.kimodoLaunchRawLead),
    appliedLead: Number(el.dataset.kimodoLaunchAppliedLead),
    physicalSpeedRatio: Number(el.dataset.kimodoLaunchPhysicalSpeedRatio),
    bodyPitch: Number(el.dataset.kimodoLaunchBodyPitch),
    pitchBias: Number(el.dataset.kimodoLaunchPitchBias),
    maxStanceSlip: Number(el.dataset.kimodoLaunchMaxStanceSlip),
    frozen: el.dataset.kimodoLaunchFrozen,
    freezeTime: Number(el.dataset.kimodoLaunchFreezeTime)
  }));

  fs.mkdirSync(outDir, { recursive: true });
  const stem = candidate ? "candidate-kimodo" : "baseline";
  await scene.screenshot({
    path: `${outDir}/${stem}-side.png`
  });

  await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("LOW");
  await page.waitForTimeout(220);
  await scene.screenshot({
    path: `${outDir}/${stem}-low.png`
  });

  return metrics;
}

test("Kimodo launch envelope changes S presentation without changing race physics", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_LAUNCH_AB_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  const baseline = await captureLaunch(page, false);
  const candidate = await captureLaunch(page, true);

  fs.writeFileSync(
    `${outDir}/metrics.json`,
    JSON.stringify({ baseline, candidate }, null, 2) + "\n"
  );

  expect(baseline.mode).toBe("baseline");
  expect(candidate.mode).toBe("candidate");
  expect(baseline.frozen).toBe("1");
  expect(candidate.frozen).toBe("1");
  expect(baseline.freezeTime).toBeCloseTo(2.1, 6);
  expect(candidate.freezeTime).toBeCloseTo(2.1, 6);
  expect(baseline.raceTime).toBeCloseTo(candidate.raceTime, 6);
  expect(baseline.physics).toBe("unchanged");
  expect(candidate.physics).toBe("unchanged");
  expect(baseline.appliedLead).toBe(0);
  expect(candidate.appliedLead).toBeGreaterThan(0.05);
  expect(Math.abs(candidate.physicalSpeedRatio - baseline.physicalSpeedRatio)).toBeLessThan(0.0001);
  expect(Math.abs(baseline.pitchBias)).toBeLessThan(0.0001);
  expect(candidate.pitchBias).toBeLessThan(-0.002);
  expect(Number.isFinite(baseline.bodyPitch)).toBeTruthy();
  expect(Number.isFinite(candidate.bodyPitch)).toBeTruthy();
  expect(Number.isFinite(candidate.maxStanceSlip)).toBeTruthy();

  await context.close();
});

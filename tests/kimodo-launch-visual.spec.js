import { test, expect } from "@playwright/test";
import fs from "node:fs";

const outDir = "artifacts/kimodo-ardy/launch-ab";

async function captureLaunch(page, candidate) {
  const query = new URLSearchParams({
    skipStart: "1",
    kimodoLaunch: candidate ? "1" : "0",
    kimodoLaunchBlend: "0.55"
  });
  await page.goto(
    `/evowild-test/preview-motion-first-race/index.html?${query.toString()}`,
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#scene")).toBeVisible();
  await page.getByRole("button", { name: "SIDE", exact: true }).click({ force: true });

  await page.waitForFunction(() => {
    const scene = document.querySelector("#scene");
    return Number(scene?.dataset.kimodoLaunchRaceTime || 0) >= 1.80;
  });
  await page.locator("#pauseButton").click({ force: true });
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
    maxStanceSlip: Number(el.dataset.kimodoLaunchMaxStanceSlip)
  }));

  fs.mkdirSync(outDir, { recursive: true });
  await scene.screenshot({
    path: `${outDir}/${candidate ? "candidate-kimodo" : "baseline"}-side.png`
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

  expect(baseline.mode).toBe("baseline");
  expect(candidate.mode).toBe("candidate");
  expect(baseline.physics).toBe("unchanged");
  expect(candidate.physics).toBe("unchanged");
  expect(baseline.appliedLead).toBe(0);
  expect(candidate.appliedLead).toBeGreaterThan(0.05);
  expect(Math.abs(candidate.physicalSpeedRatio - baseline.physicalSpeedRatio)).toBeLessThan(0.04);
  expect(candidate.bodyPitch).toBeLessThan(baseline.bodyPitch - 0.005);
  expect(Number.isFinite(candidate.maxStanceSlip)).toBeTruthy();

  fs.writeFileSync(
    `${outDir}/metrics.json`,
    JSON.stringify({ baseline, candidate }, null, 2) + "\n"
  );

  await context.close();
});

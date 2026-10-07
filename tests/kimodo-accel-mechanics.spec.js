import { test, expect } from "@playwright/test";
import fs from "node:fs";

const outDir = "artifacts/kimodo-ardy/accel-mechanics-ab";

async function captureAt(page, candidate, freezeTime, camera) {
  const query = new URLSearchParams({
    skipStart: "1",
    proxyReviewRunner: "0",
    proxyReviewCamera: camera,
    kimodoLaunch: candidate ? "1" : "0",
    kimodoLaunchSource: "accel",
    kimodoLaunchBlend: "0.55",
    kimodoLaunchFreeze: String(freezeTime)
  });

  await page.goto(
    `/evowild-test/preview-motion-first-race/index.html?${query.toString()}`,
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#loading")).toHaveClass(/hidden/);
  await expect(page.locator("#runnerSelect")).toHaveValue("0");
  await expect(page.locator("#scene")).toHaveAttribute("data-proxy-review-camera", camera);
  await expect(page.locator("#cameraReadout")).toHaveText(camera);

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
    bodyStretch: Number(el.dataset.kimodoLaunchBodyStretch),
    maxStanceSlip: Number(el.dataset.kimodoLaunchMaxStanceSlip)
  }));

  fs.mkdirSync(outDir, { recursive: true });
  const tag = freezeTime.toFixed(1).replace(".", "_");
  const stem = candidate ? "candidate" : "baseline";
  await scene.screenshot({
    path: `${outDir}/t${tag}-${stem}-${camera.toLowerCase()}.png`
  });
  return metrics;
}

test("explicit Kimodo acceleration shapes S launch mechanics without changing race physics", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_ACCEL_MECHANICS_AB !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  const evidence = {};

  for (const t of [2.1, 2.7, 3.1]) {
    evidence[t.toFixed(1)] = {};
    for (const camera of ["SIDE", "LOW"]) {
      const baseline = await captureAt(page, false, t, camera);
      const candidate = await captureAt(page, true, t, camera);
      evidence[t.toFixed(1)][camera] = { baseline, candidate };

      expect(baseline.source).toBe("accel");
      expect(candidate.source).toBe("accel");
      expect(baseline.physics).toBe("unchanged");
      expect(candidate.physics).toBe("unchanged");
      expect(baseline.raceTime).toBeCloseTo(candidate.raceTime, 6);
      expect(baseline.physicalSpeedRatio).toBeCloseTo(candidate.physicalSpeedRatio, 6);
      expect(baseline.appliedLead).toBe(0);
      expect(candidate.maxStanceSlip).toBeLessThan(0.01);
    }
  }

  const pre = evidence["2.1"].SIDE;
  const active = evidence["2.7"].SIDE;

  expect(pre.candidate.appliedLead).toBeLessThan(0.01);
  expect(Math.abs(pre.candidate.bodyStretch - pre.baseline.bodyStretch)).toBeLessThan(0.01);

  expect(active.candidate.appliedLead).toBeGreaterThan(0.05);
  expect(active.candidate.pitchBias).toBeLessThan(-0.002);
  expect(active.candidate.bodyStretch).toBeGreaterThan(active.baseline.bodyStretch + 0.015);

  fs.writeFileSync(
    `${outDir}/metrics.json`,
    JSON.stringify(evidence, null, 2) + "\n"
  );

  await context.close();
});

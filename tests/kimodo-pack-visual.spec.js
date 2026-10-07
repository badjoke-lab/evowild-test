import { test, expect } from "@playwright/test";
import fs from "node:fs";

const outDir = "artifacts/kimodo-ardy/pack-ab";

async function capturePack(page, candidate, freezeTime) {
  const query = new URLSearchParams({
    skipStart: "1",
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
  await page.getByRole("button", { name: "PACK", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("PACK");

  await page.waitForFunction(() =>
    document.querySelector("#scene")?.dataset.kimodoLaunchFrozen === "1"
  );
  await page.waitForTimeout(220);

  const scene = page.locator("#scene");
  const metrics = await scene.evaluate((el) => ({
    mode: el.dataset.kimodoLaunchMode,
    source: el.dataset.kimodoLaunchSource,
    physics: el.dataset.kimodoLaunchPhysics,
    raceTime: Number(el.dataset.kimodoLaunchRaceTime),
    physicalSpeedRatio: Number(el.dataset.kimodoLaunchPhysicalSpeedRatio),
    appliedLead: Number(el.dataset.kimodoLaunchAppliedLead),
    runnerCount: Number(el.dataset.runnerCount),
    proxyRunnerCount: Number(el.dataset.proxyRunnerCount),
    camera: document.querySelector("#cameraReadout")?.textContent
  }));

  fs.mkdirSync(outDir, { recursive: true });
  const tag = freezeTime.toFixed(1).replace(".", "_");
  await scene.screenshot({
    path: `${outDir}/t${tag}-${candidate ? "candidate" : "baseline"}-pack.png`
  });
  return metrics;
}

test("Kimodo acceleration candidate remains bounded in full 18-runner pack", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_PACK_AB !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  const evidence = {};

  for (const t of [2.7, 3.1]) {
    const baseline = await capturePack(page, false, t);
    const candidate = await capturePack(page, true, t);
    evidence[t.toFixed(1)] = { baseline, candidate };

    expect(baseline.runnerCount).toBe(18);
    expect(candidate.runnerCount).toBe(18);
    expect(baseline.proxyRunnerCount).toBe(18);
    expect(candidate.proxyRunnerCount).toBe(18);
    expect(baseline.camera).toBe("PACK");
    expect(candidate.camera).toBe("PACK");
    expect(baseline.physics).toBe("unchanged");
    expect(candidate.physics).toBe("unchanged");
    expect(baseline.physicalSpeedRatio).toBeCloseTo(candidate.physicalSpeedRatio, 6);
    expect(candidate.appliedLead).toBeGreaterThan(0.05);
  }

  fs.writeFileSync(
    `${outDir}/metrics.json`,
    JSON.stringify(evidence, null, 2) + "\n"
  );

  await context.close();
});

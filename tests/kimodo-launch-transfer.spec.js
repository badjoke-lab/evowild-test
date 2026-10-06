import { test, expect } from "@playwright/test";
import fs from "node:fs";

const OUT = "test-results/kimodo-launch";

async function setView(page, view) {
  await page.getByRole("button", { name: view, exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText(view);
  // Camera damping continues while physics is paused. Give it several render
  // frames so SIDE/LOW evidence is not captured mid-transition.
  await page.waitForTimeout(450);
}

async function capturePausedViews(page, scene, label, stage) {
  await setView(page, "SIDE");
  await scene.screenshot({ path: `${OUT}/side-${label}-${stage}.png` });
  await setView(page, "LOW");
  await scene.screenshot({ path: `${OUT}/low-${label}-${stage}.png` });
  await setView(page, "SIDE");
}

async function readTelemetry(scene) {
  return {
    simTime: Number(await scene.getAttribute("data-race-time")),
    leanTarget: Number(await scene.getAttribute("data-s-accel-lean-target")),
    lean: Number(await scene.getAttribute("data-s-accel-lean")),
    envelope: await scene.getAttribute("data-kimodo-launch-envelope"),
    review: await scene.getAttribute("data-kimodo-launch-review"),
    playback: Number(await scene.getAttribute("data-s-playback-rate")),
    seconds: await scene.getAttribute("data-kimodo-launch-seconds"),
    drive: await scene.getAttribute("data-kimodo-launch-drive"),
    neckPitchDeg: Number(await scene.getAttribute("data-kimodo-neck-pitch-deg"))
  };
}

async function captureVariant(browser, kimodo) {
  const label = kimodo ? "kimodo" : "baseline";
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: OUT,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const q = new URLSearchParams({
    motion: "1",
    morph: "S",
    launchTimingReview: "1",
    launchTimingHold: "1"
  });
  if (kimodo) q.set("kimodoLaunch", "1");

  await page.goto(
    `http://127.0.0.1:4173/evowild-test/preview-motion-first/index.html?${q}`,
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toBeVisible();
  await expect(scene).toHaveAttribute("data-s-asset-ready", "1");
  await expect(scene).toHaveAttribute("data-s-runtime-animated", "1");
  await expect(scene).toHaveAttribute("data-launch-timing-review", "1");
  await expect(scene).toHaveAttribute("data-launch-timing-hold", "1");
  await setView(page, "SIDE");

  if (kimodo) {
    await page.evaluate(() => window.__resetKimodoLaunchReview?.());
  }

  const pauseAt = async (targetSeconds) => {
    await page.evaluate((target) => {
      window.__pauseLaunchTimingReviewAt?.(target);
    }, targetSeconds);
    await page.getByRole("button", { name: "RESUME", exact: true }).click({ force: true });
    await expect.poll(
      async () => Number(await scene.getAttribute("data-launch-timing-paused-at")),
      { timeout: 20000 }
    ).toBeGreaterThanOrEqual(targetSeconds);
  };

  const samples = {};
  for (const [stage, target] of [["early", 0.5], ["mid", 1.6], ["late", 4.2]]) {
    await pauseAt(target);
    samples[stage] = await readTelemetry(scene);
    await capturePausedViews(page, scene, label, stage);
  }

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright video was not created");
  await video.saveAs(`${OUT}/${label}.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
  return samples;
}

test("Kimodo v2 launch timing preserves S root/gait and adds non-contact follow-through", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_LAUNCH_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(180000);
  fs.mkdirSync(OUT, { recursive: true });

  const baseline = await captureVariant(browser, false);
  const kimodo = await captureVariant(browser, true);

  fs.writeFileSync(
    `${OUT}/telemetry.json`,
    JSON.stringify({ baseline, kimodo }, null, 2)
  );

  expect(baseline.early.review).toBe("0");
  expect(kimodo.early.review).toBe("1");
  expect(baseline.early.envelope).toBe("baseline");
  expect(Number(kimodo.early.envelope)).toBeGreaterThan(0);
  expect(Number(kimodo.early.envelope)).toBeLessThan(1);
  expect(Number(kimodo.mid.envelope)).toBeGreaterThan(Number(kimodo.early.envelope));

  for (const stage of ["early", "mid", "late"]) {
    expect(Math.abs(baseline[stage].simTime - kimodo[stage].simTime)).toBeLessThan(0.03);
    expect(Math.abs(baseline[stage].playback - kimodo[stage].playback)).toBeLessThan(0.02);
    expect(Math.abs(baseline[stage].leanTarget - kimodo[stage].leanTarget)).toBeLessThan(0.002);
  }

  expect(Number(kimodo.early.drive)).toBeGreaterThan(Number(kimodo.mid.drive));
  expect(Number(kimodo.mid.drive)).toBeGreaterThan(0);
  expect(Number(kimodo.late.drive)).toBeLessThan(0.001);
  expect(kimodo.early.neckPitchDeg).toBeGreaterThan(2);
  expect(kimodo.early.neckPitchDeg).toBeLessThan(7.1);
});

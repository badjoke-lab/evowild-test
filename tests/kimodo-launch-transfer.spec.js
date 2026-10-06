import { test, expect } from "@playwright/test";
import fs from "node:fs";

const OUT = "test-results/kimodo-launch";

async function captureVariant(browser, view, kimodo) {
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

  await page.getByRole("button", { name: view, exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText(view);
  await expect(scene).toHaveAttribute("data-launch-timing-hold", "1");
  await page.getByRole("button", { name: "RESUME", exact: true }).click({ force: true });

  await page.waitForTimeout(500);
  const early = {
    leanTarget: Number(await scene.getAttribute("data-s-accel-lean-target")),
    lean: Number(await scene.getAttribute("data-s-accel-lean")),
    envelope: await scene.getAttribute("data-kimodo-launch-envelope"),
    review: await scene.getAttribute("data-kimodo-launch-review"),
    playback: Number(await scene.getAttribute("data-s-playback-rate"))
  };

  await page.waitForTimeout(1100);
  const mid = {
    leanTarget: Number(await scene.getAttribute("data-s-accel-lean-target")),
    lean: Number(await scene.getAttribute("data-s-accel-lean")),
    envelope: await scene.getAttribute("data-kimodo-launch-envelope"),
    review: await scene.getAttribute("data-kimodo-launch-review"),
    playback: Number(await scene.getAttribute("data-s-playback-rate"))
  };

  await page.waitForTimeout(2500);

  await scene.screenshot({
    path: `${OUT}/${view.toLowerCase()}-${label}-late.png`
  });

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright video was not created");
  await video.saveAs(`${OUT}/${view.toLowerCase()}-${label}.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  return { early, mid };
}

test("Kimodo launch timing review preserves S gait runtime and changes only posture timing", async ({ browser }, testInfo) => {
  test.skip(process.env.KIMODO_LAUNCH_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);
  fs.mkdirSync(OUT, { recursive: true });

  const baselineSide = await captureVariant(browser, "SIDE", false);
  const kimodoSide = await captureVariant(browser, "SIDE", true);
  await captureVariant(browser, "LOW", false);
  await captureVariant(browser, "LOW", true);

  expect(baselineSide.early.review).toBe("0");
  expect(kimodoSide.early.review).toBe("1");
  expect(baselineSide.early.envelope).toBe("baseline");
  expect(Number(kimodoSide.early.envelope)).toBeGreaterThan(0);
  expect(Number(kimodoSide.mid.envelope)).toBeGreaterThan(Number(kimodoSide.early.envelope));

  expect(Number.isFinite(baselineSide.early.playback)).toBeTruthy();
  expect(Number.isFinite(kimodoSide.early.playback)).toBeTruthy();

  // Kimodo changes the launch lean timing, not the baked S gait playback rule.
  expect(Math.abs(kimodoSide.early.playback - baselineSide.early.playback)).toBeLessThan(0.12);

  // By the middle of the launch, the faster Kimodo establishment envelope
  // should have returned the visual launch lean toward neutral sooner.
  expect(kimodoSide.mid.leanTarget).toBeLessThan(baselineSide.mid.leanTarget);
});

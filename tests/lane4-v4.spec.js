import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Lane 4 runs with animated EvoWild S racers", async ({ page }, testInfo) => {
  test.setTimeout(150000);
  const errors = [];
  page.on("pageerror", (err) => errors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  const response = await page.goto(
    "/evowild-test/lane4-v4/?ciNoPrewarm=1&ciRace=1&quality=low&scale=0.5&scaler=0.5",
    { waitUntil: "domcontentloaded" }
  );
  expect(response?.status()).toBeLessThan(400);
  await expect(page).toHaveTitle("Kart Royale");

  await page.waitForFunction(() => Boolean(window.__ctx?.race), null, { timeout: 90000 });
  await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 90000 });
  await page.waitForFunction(
    () => document.documentElement.dataset.evowildRacers === "ready",
    null,
    { timeout: 90000 }
  );

  const visual = await page.evaluate(() => ({
    status: document.documentElement.dataset.evowildRacers,
    count: document.documentElement.dataset.evowildRacerCount,
    model: document.documentElement.dataset.evowildRacerModel,
    clip: document.documentElement.dataset.evowildRacerClip,
    exposed: window.__evowildRacers
  }));
  console.log("EVOWILD_RACER_VISUAL", JSON.stringify(visual));
  expect(visual.status).toBe("ready");
  expect(Number(visual.count)).toBe(8);
  expect(visual.model).toBe("hunyuan-rigged-s");
  expect(visual.clip).toBe("EvoWild_S_Run");

  await page.waitForFunction(
    () => document.documentElement.dataset.ciRace === "racing" && window.__ctx?.race?.state === 2,
    null,
    { timeout: 90000 }
  );
  const firstFrame = await page.evaluate(() => window.__ctx.frame);
  await page.waitForFunction(
    (frame) => window.__ctx?.frame >= frame + 8,
    firstFrame,
    { timeout: 90000 }
  );

  fs.mkdirSync("test-results/visuals", { recursive: true });
  const filename = testInfo.project.name === "android-chromium"
    ? "test-results/visuals/android-lane4-evowild-s.png"
    : "test-results/visuals/desktop-lane4-evowild-s.png";
  await page.screenshot({ path: filename, fullPage: true });

  const state = await page.evaluate(() => ({
    state: window.__ctx.race.state,
    autoDrive: window.__ctx.race.autoDrive,
    karts: window.__ctx.race.karts.length,
    frame: window.__ctx.frame,
    ready: window.__gameReady,
    visuals: window.__evowildRacers
  }));
  console.log("LANE4_EVOWILD_STATE", JSON.stringify(state));
  expect(state.autoDrive).toBe(true);
  expect(state.karts).toBe(8);
  expect(state.frame).toBeGreaterThan(8);
  expect(state.visuals?.animation).toBe("EvoWild_S_Run");
  expect(errors, errors.join("\n")).toEqual([]);
});

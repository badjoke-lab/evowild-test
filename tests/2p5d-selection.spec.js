import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("2.5D selection capture - Lane 4 V5", async ({ page }, testInfo) => {
  test.setTimeout(180000);
  const errors = [];
  page.on("pageerror", e => errors.push(e.stack || String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  const response = await page.goto(
    "/evowild-test/lane4-v4/?evowild=1&ciNoPrewarm=1&quality=high&scale=0.75&scaler=0.75",
    { waitUntil: "domcontentloaded", timeout: 90000 }
  );
  expect(response?.status()).toBeLessThan(400);
  await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 120000 });
  await page.waitForFunction(() => window.__evowildSReady === true || Boolean(window.__evowildSError), null, { timeout: 30000 });
  expect(await page.evaluate(() => window.__evowildSError)).toBeFalsy();

  await page.evaluate(() => {
    const { race, track } = window.__ctx;
    race.autoDrive = true;
    race.start();
    race.state = 2;
    const mark = 0.14;
    const baseSpeed = 24;
    race.karts.forEach((k, i) => {
      const t = ((mark - i * 0.0045) % 1 + 1) % 1;
      const smp = track.sample(t);
      const lane = ((i % 2) * 2 - 1) * (1.8 + (i >> 1) * 0.42);
      const p = smp.pos.clone().addScaledVector(smp.binormal, lane);
      k.placeAt?.(p, Math.atan2(smp.tangent.x, smp.tangent.z), t);
      k.velocity.copy(k.forward).multiplyScalar(baseSpeed - Math.min(i * 0.28, 1.6));
    });
  });

  await page.waitForTimeout(2400);
  fs.mkdirSync("artifacts/2p5d-selection", { recursive: true });
  await page.screenshot({
    path: `artifacts/2p5d-selection/lane4-v5-${testInfo.project.name}-early.png`,
    fullPage: true
  });
  await page.waitForTimeout(4200);
  await page.screenshot({
    path: `artifacts/2p5d-selection/lane4-v5-${testInfo.project.name}-mid.png`,
    fullPage: true
  });
  expect(errors, errors.join("\n")).toEqual([]);
});
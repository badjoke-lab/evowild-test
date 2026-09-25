import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Lane 4 V5 runs S field on intact Kart Royale world", async ({ page }) => {
  test.setTimeout(180000);
  const errors = [];
  page.on("pageerror", (err) => errors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  const response = await page.goto(
    "/evowild-test/lane4-v4/?evowild=1&ciNoPrewarm=1&quality=high&scale=0.75&scaler=0.75",
    { waitUntil: "domcontentloaded", timeout: 90000 }
  );
  expect(response?.status()).toBeLessThan(400);
  await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 120000 });
  await page.waitForFunction(() => window.__evowildSReady === true, null, { timeout: 30000 });

  await page.evaluate(() => {
    const ctx = window.__ctx;
    const race = ctx.race;
    const track = ctx.track;
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

  const proof = await page.evaluate(() => ({
    ready: window.__evowildSReady,
    sprites: document.querySelectorAll("canvas").length,
    raceState: window.__ctx.race.state,
    karts: window.__ctx.race.karts.length,
    speed: Math.hypot(window.__ctx.race.player.velocity.x, window.__ctx.race.player.velocity.z)
  }));
  expect(proof.ready).toBe(true);
  expect(proof.raceState).toBe(2);
  expect(proof.karts).toBeGreaterThan(1);
  expect(proof.speed).toBeGreaterThan(10);
  expect(errors, errors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals", { recursive: true });
  await page.screenshot({
    path: "test-results/visuals/desktop-lane4-v5-s-kart-royale.png",
    fullPage: true
  });
});

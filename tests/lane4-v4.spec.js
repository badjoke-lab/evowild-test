import { test, expect } from "@playwright/test";
import fs from "node:fs";

for (const project of ["desktop-chromium", "android-chromium"]) {
  test(`Kart Royale intact baseline renders and races on ${project}`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== project);
    test.setTimeout(180000);

    const errors = [];
    page.on("pageerror", (err) => errors.push(err.stack || String(err)));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    const mobile = testInfo.project.name === "android-chromium";
    if (mobile) await page.setViewportSize({ width: 915, height: 412 });

    const quality = mobile ? "low" : "high";
    const scale = mobile ? "0.5" : "0.75";
    const response = await page.goto(
      `/evowild-test/lane4-v4/?ciNoPrewarm=1&quality=${quality}&scale=${scale}&scaler=${scale}`,
      { waitUntil: "domcontentloaded", timeout: 90000 }
    );
    expect(response?.status()).toBeLessThan(400);
    await expect(page).toHaveTitle("Kart Royale");

    await page.waitForFunction(() => Boolean(window.__ctx?.race), null, { timeout: 120000 });
    await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 120000 });

    await page.evaluate(() => {
      window.__ctx.race.autoDrive = true;
      window.__ctx.race.start();
    });

    await page.waitForFunction(() => window.__ctx?.race?.state === 2, null, { timeout: 15000 });
    await page.waitForFunction(() => {
      const p = window.__ctx?.race?.player;
      return !!p && Math.hypot(p.velocity.x, p.velocity.z) >= 18;
    }, null, { timeout: 30000 });
    await page.waitForTimeout(1800);

    fs.mkdirSync("test-results/visuals", { recursive: true });
    const filename = mobile
      ? "test-results/visuals/android-lane4-kart-royale.png"
      : "test-results/visuals/desktop-lane4-kart-royale.png";
    await page.screenshot({ path: filename, fullPage: true });

    const state = await page.evaluate(() => {
      const p = window.__ctx.race.player;
      return {
        state: window.__ctx.race.state,
        autoDrive: window.__ctx.race.autoDrive,
        karts: window.__ctx.race.karts.length,
        frame: window.__ctx.frame,
        ready: window.__gameReady,
        speed: Math.hypot(p.velocity.x, p.velocity.z),
        viewport: [innerWidth, innerHeight]
      };
    });
    console.log("KART_ROYALE_BASELINE", JSON.stringify(state));
    expect(state.autoDrive).toBe(true);
    expect(state.karts).toBeGreaterThan(1);
    expect(state.frame).toBeGreaterThan(8);
    expect(state.speed).toBeGreaterThanOrEqual(18);
    expect(errors, errors.join("\n")).toEqual([]);
  });
}

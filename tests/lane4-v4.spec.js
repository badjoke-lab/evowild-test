import { test, expect } from "@playwright/test";
import fs from "node:fs";

for (const project of ["desktop-chromium", "android-chromium"]) {
  test(`Kart Royale intact baseline renders and races on ${project}`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== project);

    const errors = [];
    page.on("pageerror", (err) => errors.push(err.stack || String(err)));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    const response = await page.goto("/evowild-test/lane4-v4/?ciNoPrewarm=1&quality=low&scale=0.5&scaler=0.5", { waitUntil: "domcontentloaded" });
    expect(response?.status()).toBeLessThan(400);
    await expect(page).toHaveTitle("Kart Royale");

    await page.waitForFunction(() => Boolean(window.__ctx?.race), null, { timeout: 90000 });
    await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 90000 });
    await page.evaluate(() => {
      window.__ctx.race.autoDrive = true;
      window.__ctx.race.start();
      window.__ctx.race.state = 2;
    });

    await page.waitForFunction(() => window.__ctx?.race?.state === 2, null, { timeout: 5000 });
    await page.waitForTimeout(5000);

    fs.mkdirSync("test-results/visuals", { recursive: true });
    const filename = testInfo.project.name === "android-chromium"
      ? "test-results/visuals/android-lane4-kart-royale.png"
      : "test-results/visuals/desktop-lane4-kart-royale.png";
    await page.screenshot({ path: filename, fullPage: true });

    const state = await page.evaluate(() => ({
      state: window.__ctx.race.state,
      autoDrive: window.__ctx.race.autoDrive,
      karts: window.__ctx.race.karts.length,
      frame: window.__ctx.frame,
      ready: window.__gameReady
    }));
    console.log("KART_ROYALE_BASELINE", JSON.stringify(state));
    expect(state.autoDrive).toBe(true);
    expect(state.karts).toBeGreaterThan(1);
    expect(state.frame).toBeGreaterThan(8);
    expect(errors, errors.join("\n")).toEqual([]);
  });
}

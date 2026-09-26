import { test, expect } from "@playwright/test";
import fs from "node:fs";

for (const project of ["desktop-chromium", "android-chromium"]) {
  test(`EvoWild S runs on borrowed Kart Royale base on ${project}`, async ({ page }, testInfo) => {
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
      `/evowild-test/lane4-v4/?ciNoPrewarm=1&quality=${quality}&scale=${scale}&scaler=${scale}&evowildS=1&evowildSpectator=1`,
      { waitUntil: "domcontentloaded", timeout: 90000 }
    );
    expect(response?.status()).toBeLessThan(400);
    await expect(page).toHaveTitle("Kart Royale");

    await page.waitForFunction(() => Boolean(window.__ctx?.race), null, { timeout: 120000 });
    await page.waitForFunction(() => window.__gameReady === true, null, { timeout: 120000 });

    await page.evaluate(() => {
      const ctx = window.__ctx;
      const race = ctx.race;
      const track = ctx.track;
      race.autoDrive = true;
      race.start();
      race.state = 2;

      const mark = 0.06;
      const baseSpeed = 24;
      race.karts.forEach((k, i) => {
        const row = Math.floor(i / 2);
        const t = ((mark - row * 0.0014) % 1 + 1) % 1;
        const smp = track.sample(t);
        const lane = i % 2 === 0 ? -1.7 - row * 0.18 : 1.7 + row * 0.18;
        const p = smp.pos.clone().addScaledVector(smp.binormal, lane);
        k.placeAt?.(p, Math.atan2(smp.tangent.x, smp.tangent.z), t);
        k.velocity.copy(k.forward).multiplyScalar(baseSpeed - row * 0.45);
      });
    });

    await page.waitForFunction(() => {
      const race = window.__ctx?.race;
      if (!race || race.karts.length !== 8) return false;
      return race.karts.every((k) => {
        const s = k.object.getObjectByName("evowildS");
        const image = s?.material?.map?.image;
        return Boolean(s && image && (image.width || image.naturalWidth || 0) > 0);
      });
    }, null, { timeout: 30000 });
    await page.waitForTimeout(2200);
    const animBefore = await page.evaluate(() =>
      window.__ctx.race.karts.map((k) => k.object.getObjectByName("evowildS")?.userData?.animSerial ?? -1)
    );
    await page.waitForTimeout(320);
    const animAfter = await page.evaluate(() =>
      window.__ctx.race.karts.map((k) => k.object.getObjectByName("evowildS")?.userData?.animSerial ?? -1)
    );
    expect(animAfter.some((v, i) => v > animBefore[i])).toBe(true);

    const state = await page.evaluate(() => {
      const race = window.__ctx.race;
      const p = race.player;
      let visibleKartDetails = 0;
      let loadedSprites = 0;
      for (const k of race.karts) {
        const s = k.object.getObjectByName("evowildS");
        const image = s?.material?.map?.image;
        if (s && image && (image.width || image.naturalWidth || 0) > 0) loadedSprites++;
        k.object.traverse((o) => {
          const detail = o.userData?.detailNodes;
          if (Array.isArray(detail)) {
            for (const node of detail) if (node.visible) visibleKartDetails++;
          }
        });
      }
      return {
        state: race.state,
        karts: race.karts.length,
        sSprites: race.karts.filter((k) => Boolean(k.object.getObjectByName("evowildS"))).length,
        loadedSprites,
        visibleKartDetails,
        speed: Math.hypot(p.velocity.x, p.velocity.z),
        frame: window.__ctx.frame,
        viewport: [innerWidth, innerHeight]
      };
    });

    expect(state.state).toBe(2);
    expect(state.karts).toBe(8);
    expect(state.sSprites).toBe(8);
    expect(state.loadedSprites).toBe(8);
    expect(state.visibleKartDetails).toBe(0);
    expect(state.speed).toBeGreaterThan(10);
    expect(state.frame).toBeGreaterThan(8);
    expect(errors, errors.join("\n")).toEqual([]);

    fs.mkdirSync("test-results/evowild-s", { recursive: true });
    const filename = mobile
      ? "test-results/evowild-s/android-lane4-s.png"
      : "test-results/evowild-s/desktop-lane4-s.png";
    await page.screenshot({ path: filename, fullPage: true });

    console.log("EVOWILD_S_ON_KART_ROYALE", JSON.stringify(state));
  });
}

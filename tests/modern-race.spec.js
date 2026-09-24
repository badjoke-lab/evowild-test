import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("record modern clean-room 2.5D race proof", async ({ browser }, testInfo) => {
  test.setTimeout(35000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/modern-visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/race-modern-proof.html", { waitUntil: "networkidle" });

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-proof", "modern-2p5d");
  await expect(stage).toHaveAttribute("data-ready", "true", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-sprite-sheet", "loaded", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-mode", "modern-hd-side", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-resolution", "1280x720", { timeout: 10000 });

  await page.waitForTimeout(3800);
  await page.screenshot({ path: `${outDir}/modern-race-early.png`, fullPage: true });
  await page.waitForTimeout(4200);
  await page.screenshot({ path: `${outDir}/modern-race-late.png`, fullPage: true });

  const video = page.video();
  await page.close();
  const raw = await video.path();
  fs.renameSync(raw, `${outDir}/modern-race.webm`);
  await context.close();
});

import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("record pseudo-3D S race proof", async ({ browser }, testInfo) => {
  const dir = "test-results/visuals";
  fs.mkdirSync(dir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();

  await page.goto("http://127.0.0.1:4173/evowild-test/mode7.html?capture=1");
  await expect(page.locator("#race")).toHaveAttribute("data-s-sheet", "loaded", { timeout: 12000 });
  await expect(page.locator("#race")).toHaveAttribute("data-state", "running", { timeout: 12000 });
  await expect(page.locator("#race")).toHaveAttribute("data-renderer", "pseudo3d-segment-projection");

  await page.waitForTimeout(3200);
  await page.screenshot({ path: dir + "/mode7-race.png" });

  await page.waitForTimeout(3200);
  await page.screenshot({ path: dir + "/mode7-race-late.png" });

  const video = page.video();
  await context.close();
  if (video) await video.saveAs(dir + "/mode7-race.webm");

  await testInfo.attach("mode7-race", {
    path: dir + "/mode7-race.png",
    contentType: "image/png"
  });
});

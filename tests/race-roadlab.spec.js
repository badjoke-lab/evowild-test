import { test, expect } from "@playwright/test";
import fs from "node:fs";

async function assertRunning(page, shot) {
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(String(err)));

  await page.goto(`/evowild-test/race-roadlab.html?shot=${shot}`, { waitUntil: "networkidle" });
  const stage = page.locator(".roadlab");

  await expect(stage).toHaveAttribute("data-state", "ready", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-running", "true", { timeout: 5000 });
  await expect(stage).toHaveAttribute("data-loaded-morphs", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-direction-set", "five-directions-all-morphs");
  await expect(stage).toHaveAttribute("data-loaded-direction-target", "side,front_3q,front,back_3q,back");
  await expect(stage).toHaveAttribute("data-camera-mode", shot === "front3q" ? "front_3q" : shot === "back3q" ? "back_3q" : shot);

  const expectedDirection = shot === "front3q" ? "front_3q" : shot === "back3q" ? "back_3q" : shot;
  await expect(stage).toHaveAttribute("data-selected-direction", expectedDirection, { timeout: 5000 });

  const frames = new Set();
  for (let i = 0; i < 5; i++) {
    frames.add(await stage.getAttribute("data-frame"));
    await page.waitForTimeout(110);
  }
  expect(frames.size).toBeGreaterThanOrEqual(2);
  expect(pageErrors).toEqual([]);
  return stage;
}

test("Road Lab renders animated S/P/E/A morph race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Road Lab visual proof runs on desktop only");
  test.setTimeout(45000);

  fs.mkdirSync("test-results/visuals", { recursive: true });

  for (const shot of ["side","front3q","back3q"]) {
    const stage = await assertRunning(page, shot);
    await page.waitForTimeout(900);
    await stage.screenshot({
      path: `test-results/visuals/desktop-roadlab-${shot}.png`,
      animations: "disabled"
    });
  }
});

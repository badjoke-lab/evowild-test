import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Road Lab renders animated S/P/E/A morph race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Road Lab visual proof runs on desktop only");
  test.setTimeout(45000);
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(String(err)));

  await page.goto("/evowild-test/race-roadlab.html", { waitUntil: "networkidle" });
  const stage = page.locator(".roadlab");

  await expect(stage).toHaveAttribute("data-state", "ready", { timeout: 10000 });
  await page.waitForTimeout(700);
  console.log("ROADLAB_DEBUG", JSON.stringify({
    running: await stage.getAttribute("data-running"),
    runtimeError: await stage.getAttribute("data-runtime-error"),
    pageErrors
  }));
  await expect(stage).toHaveAttribute("data-running", "true", { timeout: 5000 });
  await expect(stage).toHaveAttribute("data-loaded-morphs", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-direction-set", "five-directions-all-morphs");
  await expect(stage).toHaveAttribute("data-loaded-direction-target", "side,front_3q,front,back_3q,back");

  const frames = new Set();
  for (let i = 0; i < 5; i++) {
    frames.add(await stage.getAttribute("data-frame"));
    await page.waitForTimeout(110);
  }
  expect(frames.size).toBeGreaterThanOrEqual(2);
  expect(pageErrors).toEqual([]);

  if (testInfo.project.name === "desktop-chromium") {
    fs.mkdirSync("test-results/visuals", { recursive: true });
    await page.waitForTimeout(1200);
    await stage.screenshot({
      path: "test-results/visuals/desktop-roadlab.png",
      animations: "disabled"
    });
  }
});

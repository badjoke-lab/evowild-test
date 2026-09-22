import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("race scene renders and advances", async ({ page }) => {
  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);

  const state = {
    clock: await page.locator("#clock").textContent(),
    position: await page.locator("#position").textContent(),
    pauseLabel: await page.locator("#pause").textContent(),
    pageErrors,
    consoleErrors
  };
  console.log("RUNTIME_STATE", JSON.stringify(state));

  await expect(page.locator("#game")).toBeVisible();
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "running", { timeout: 6500 });
  await expect(page.locator("#clock")).not.toHaveText("00:00.00", { timeout: 5000 });
  await expect(page.locator("#position")).not.toHaveText("— / 18", { timeout: 5000 });
  await expect(page.locator(".runtime-status")).toBeHidden({ timeout: 5000 });

  const canvasInfo = await page.locator("#game").evaluate((canvas) => ({
    width: canvas.width,
    height: canvas.height,
    cssWidth: canvas.getBoundingClientRect().width,
    cssHeight: canvas.getBoundingClientRect().height
  }));

  expect(canvasInfo.width).toBeGreaterThan(0);
  expect(canvasInfo.height).toBeGreaterThan(0);
  expect(canvasInfo.cssWidth).toBeGreaterThan(0);
  expect(canvasInfo.cssHeight).toBeGreaterThan(0);
});


test("capture mobile race camera views", async ({ page }, testInfo) => {
  test.setTimeout(70000);
  test.skip(testInfo.project.name !== "android-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  await page.getByRole("button", { name: "1 Morph" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
  await expect(page.locator("#stage")).toHaveAttribute("data-s-asset", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-concept-morphs", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-race2p5d", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-cycle", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-frames", "6", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-sheet", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-source", "sprite-sheet", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-animated-racers", "5", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-follow-occlusion-fade", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-presentation", "v4", { timeout: 8000 });
  for (const morph of ["S", "P", "E", "A"]) {
    await page.locator(`[data-morph="${morph}"]`).click();
    await page.waitForTimeout(350);
    await page.locator("#stage").screenshot({ path: `${outDir}/android-morph-${morph}.png` });
  }

  const views = [
    ["race", "2 Race", "RACE VIEW"],
    ["follow", "3 Follow", "FOLLOW VIEW"],
    ["tactical", "4 Tactical", "TACTICAL VIEW"]
  ];

  for (const [name, buttonText, label] of views) {
    await page.getByRole("button", { name: buttonText }).click();
    await expect(page.locator("#viewLabel")).toHaveText(label);
    if (name === "race") {
      await expect(page.locator("#stage")).toHaveAttribute("data-race-camera", "wide-pack", { timeout: 8000 });
    }
    await page.waitForTimeout(900);
    await page.locator("#stage").screenshot({ path: `${outDir}/android-${name}.png` });
  }

  await page.getByRole("button", { name: "3 Follow" }).click();
  const observedFrames = new Set();
  const observedPhases = new Set();
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(110);
    observedFrames.add(await page.locator("#stage").getAttribute("data-s-run-frame"));
    observedPhases.add(await page.locator("#stage").getAttribute("data-s-run-phase"));
  }
  expect(observedFrames.size).toBeGreaterThanOrEqual(4);
  expect(observedPhases.size).toBeGreaterThanOrEqual(4);
  await page.locator("#stage").screenshot({ path: `${outDir}/android-s-run-proof.png` });
});


test("record 2.5D race speed proof", async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } }
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/evowild-test/?proof=s-run", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race2p5d", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-cycle", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-frames", "6", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-sheet", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-source", "sprite-sheet", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-animated-racers", "5", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-follow-occlusion-fade", "enabled", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-track-presentation", "v4", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-s-run-proof", "isolated", { timeout: 8000 });
  await page.getByRole("button", { name: "3 Follow" }).click();
  await page.waitForTimeout(7200);
  const video = page.video();
  await page.close();
  const raw = await video.path();
  const finalPath = `${outDir}/desktop-2p5d-animated-s-proof.webm`;
  fs.renameSync(raw, finalPath);
  await context.close();
});


test("race reaches results and rematch returns to countdown", async ({ page }, testInfo) => {
  test.setTimeout(30000);
  test.skip(testInfo.project.name !== "desktop-chromium");

  await page.goto("/evowild-test/?proof=finish", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-distance", "45");
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "finished", { timeout: 18000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-finish-count", "18");
  await expect(page.locator("#resultsPanel")).toBeVisible();
  await expect(page.locator("#resultsList .result-row")).toHaveCount(18);
  await expect(page.locator("#resultHeadline")).toContainText("Aster");

  await page.getByRole("button", { name: "Rematch" }).click();
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "countdown");
  await expect(page.locator("#resultsPanel")).toBeHidden();
});

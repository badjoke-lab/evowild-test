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
  test.skip(testInfo.project.name !== "android-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  await page.getByRole("button", { name: "1 Morph" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
  await expect(page.locator("#stage")).toHaveAttribute("data-s-asset", "loaded", { timeout: 8000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-concept-morphs", "loaded", { timeout: 8000 });
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
    await page.waitForTimeout(900);
    await page.locator("#stage").screenshot({ path: `${outDir}/android-${name}.png` });
  }
});


test("lane 4 v2 runs vendored upstream race engine", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", (err) => errors.push(err.stack || String(err)));
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });

  await page.goto("/evowild-test/race-2_5d-lane4.html", { waitUntil: "networkidle" });
  await expect(page.locator("#lane4-status")).toHaveAttribute("data-upstream", "running", { timeout: 10000 });

  const first = Number(await page.locator("#lane4-status").getAttribute("data-base-z"));
  await page.waitForTimeout(1800);
  const second = Number(await page.locator("#lane4-status").getAttribute("data-base-z"));

  expect(second).toBeGreaterThan(first);
  expect(errors, errors.join("\n")).toEqual([]);
  await expect(page.locator("canvas")).toBeVisible();

  fs.mkdirSync("test-results/visuals", { recursive: true });
  const lane4Shot = testInfo.project.name === "android-chromium"
    ? "test-results/visuals/android-lane4-upstream-v2.png"
    : "test-results/visuals/desktop-lane4-upstream-v2.png";
  await page.screenshot({ path: lane4Shot, fullPage: true });
});

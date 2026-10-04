import { test, expect } from "@playwright/test";
import fs from "node:fs";

function attachErrorCapture(page) {
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  return { pageErrors, consoleErrors };
}

test("Visual Shader Lab V0 renders shader ON/OFF evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const { pageErrors, consoleErrors } = attachErrorCapture(page);
  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/visual-shader-lab.html", { waitUntil: "networkidle" });
  await expect(page.locator("#shader-lab-canvas")).toBeVisible();
  await expect(page.locator("#mode")).toHaveText("SHADER ON");

  await page.waitForTimeout(1600);
  await expect(page.locator("#fps")).not.toHaveText("FPS --");
  await page.screenshot({
    path: `${outDir}/v0-shader-on.png`,
    fullPage: true
  });

  await page.getByRole("button", { name: "Toggle shader" }).click();
  await expect(page.locator("#mode")).toHaveText("SHADER OFF");
  await page.waitForTimeout(900);
  await page.screenshot({
    path: `${outDir}/v0-shader-off.png`,
    fullPage: true
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

test("Visual Shader Lab V1 renders wind grass ON/OFF evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const { pageErrors, consoleErrors } = attachErrorCapture(page);
  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/visual-shader-lab.html", { waitUntil: "networkidle" });
  await expect(page.locator("#shader-lab-canvas")).toBeVisible();
  await expect(page.locator("#grassMode")).toHaveText("GRASS ON");

  await page.waitForTimeout(1800);
  await expect(page.locator("#fps")).not.toHaveText("FPS --");
  await page.screenshot({
    path: `${outDir}/v1-grass-on.png`,
    fullPage: true
  });

  await page.getByRole("button", { name: "Toggle grass" }).click();
  await expect(page.locator("#grassMode")).toHaveText("GRASS OFF");
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: `${outDir}/v1-grass-off.png`,
    fullPage: true
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Visual Shader Lab V1 records continuous wind review", async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();
  const { pageErrors, consoleErrors } = attachErrorCapture(page);

  await page.goto("http://127.0.0.1:4173/evowild-test/visual-shader-lab.html", {
    waitUntil: "networkidle"
  });
  await expect(page.locator("#grassMode")).toHaveText("GRASS ON");
  await page.waitForTimeout(3200);

  const video = page.video();
  await page.close();
  if (!video) throw new Error("V1 wind review video was not created");
  await video.saveAs(`${outDir}/v1-wind-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Visual Shader Lab V2 renders dust ON/OFF evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const { pageErrors, consoleErrors } = attachErrorCapture(page);
  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/visual-shader-lab.html", { waitUntil: "networkidle" });
  await expect(page.locator("#dustMode")).toHaveText("DUST ON");

  await page.waitForTimeout(2600);
  await page.screenshot({
    path: `${outDir}/v2-dust-on.png`,
    fullPage: true
  });

  await page.getByRole("button", { name: "Toggle dust" }).click();
  await expect(page.locator("#dustMode")).toHaveText("DUST OFF");
  await page.waitForTimeout(900);
  await page.screenshot({
    path: `${outDir}/v2-dust-off.png`,
    fullPage: true
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

test("Visual Shader Lab V2 records continuous dust review", async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();
  const { pageErrors, consoleErrors } = attachErrorCapture(page);

  await page.goto("http://127.0.0.1:4173/evowild-test/visual-shader-lab.html", {
    waitUntil: "networkidle"
  });
  await expect(page.locator("#dustMode")).toHaveText("DUST ON");
  await page.waitForTimeout(3600);

  const video = page.video();
  await page.close();
  if (!video) throw new Error("V2 dust review video was not created");
  await video.saveAs(`${outDir}/v2-dust-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Visual Shader Lab V3 renders lighting ON/OFF evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const { pageErrors, consoleErrors } = attachErrorCapture(page);
  const outDir = "artifacts/shader-lab";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/visual-shader-lab.html", { waitUntil: "networkidle" });
  await expect(page.locator("#lightMode")).toHaveText("LIGHTING ON");

  await page.getByRole("button", { name: "Toggle dust" }).click();
  await expect(page.locator("#dustMode")).toHaveText("DUST OFF");
  await page.waitForTimeout(1200);

  await page.screenshot({
    path: `${outDir}/v3-lighting-on.png`,
    fullPage: true
  });

  await page.getByRole("button", { name: "Toggle lighting" }).click();
  await expect(page.locator("#lightMode")).toHaveText("LIGHTING OFF");
  await page.waitForTimeout(180);

  await page.screenshot({
    path: `${outDir}/v3-lighting-off.png`,
    fullPage: true
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

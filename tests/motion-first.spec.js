import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Motion First S runner renders and captures required camera views", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  const pageErrors = [];
  const consoleErrors = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/preview-motion-first/index.html?inspect=1", { waitUntil: "networkidle" });
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#runnerSelect")).toHaveValue("0");

  await expect(page.locator("#raceState")).toHaveText("INSPECT");
  await page.waitForTimeout(600);

  const views = ["SIDE", "LOW", "CHASE", "FRONT"];

  for (const view of views) {
    await page.getByRole("button", { name: view, exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(650);
    await page.locator("#scene").screenshot({
      path: `${outDir}/motion-first-s-${view.toLowerCase()}.png`
    });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});



test("Motion First S gait records continuous SIDE and LOW review video", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(60000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-gait/index.html", {
    waitUntil: "networkidle"
  });
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#raceState")).toHaveText("MOTION REVIEW");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(4200);

  await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("LOW");
  await page.waitForTimeout(4200);

  await expect(page.locator("#scene")).toHaveAttribute("data-ik-clamped", "0");
  const stanceSlip = Number(await page.locator("#scene").getAttribute("data-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const bodyStretch = Number(await page.locator("#scene").getAttribute("data-max-body-stretch"));
  expect(Number.isFinite(bodyStretch)).toBeTruthy();
  expect(bodyStretch).toBeGreaterThan(0.14);

  const video = page.video();
  await page.close();

  if (!video) throw new Error("Playwright video was not created");
  await video.saveAs(`${outDir}/motion-first-s-gait-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First S Phase C records moving multi-camera transitions", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(75000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-gait/index.html", {
    waitUntil: "networkidle"
  });
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#raceState")).toHaveText("MOTION REVIEW");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  const sequence = [
    ["SIDE", 1800],
    ["CHASE", 2200],
    ["LOW", 2200],
    ["FRONT", 2200],
    ["SIDE", 2200]
  ];

  for (const [index, [view, holdMs]] of sequence.entries()) {
    if (view !== "SIDE" || (await page.locator("#cameraReadout").textContent()) !== "SIDE") {
      await page.getByRole("button", { name: view, exact: true }).click({ force: true });
      await expect(page.locator("#cameraReadout")).toHaveText(view);
    }
    await page.waitForTimeout(holdMs);

    const scene = page.locator("#scene");
    const minX = Number(await scene.getAttribute("data-focus-min-x"));
    const maxX = Number(await scene.getAttribute("data-focus-max-x"));
    const minY = Number(await scene.getAttribute("data-focus-min-y"));
    const maxY = Number(await scene.getAttribute("data-focus-max-y"));
    const width = Number(await scene.getAttribute("data-focus-width"));
    const height = Number(await scene.getAttribute("data-focus-height"));

    for (const value of [minX, maxX, minY, maxY, width, height]) {
      expect(Number.isFinite(value)).toBeTruthy();
    }

    expect(minX, `${view} clips left`).toBeGreaterThan(-0.96);
    expect(maxX, `${view} clips right`).toBeLessThan(0.96);
    expect(minY, `${view} clips bottom`).toBeGreaterThan(-0.96);
    expect(maxY, `${view} clips top`).toBeLessThan(0.96);
    expect(width, `${view} is framed too small`).toBeGreaterThan(0.20);
    expect(height, `${view} is framed too small`).toBeGreaterThan(0.20);

    await scene.screenshot({
      path: `${outDir}/motion-first-s-phase-c-${String(index).padStart(2, "0")}-${view.toLowerCase()}.png`
    });
  }

  await expect(page.locator("#scene")).toHaveAttribute("data-ik-clamped", "0");

  const video = page.video();
  await page.close();

  if (!video) throw new Error("Phase C video was not created");
  await video.saveAs(`${outDir}/motion-first-s-phase-c-multiview.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

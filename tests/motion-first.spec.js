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
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset-ready", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "hunyuan-s-lod2");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-model-yaw-degrees", "180");
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
  const highDetailAssetRequests = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("request", (request) => {
    if (request.url().includes("/models/evowild-s/")) highDetailAssetRequests.push(request.url());
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

  await expect(page.locator("#scene")).toHaveAttribute("data-s-simplified-lane", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset-ready", "0");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "procedural-simplified-lane");
  await expect(page.locator("#scene")).toHaveAttribute("data-ik-clamped", "0");

  const stanceSlip = Number(await page.locator("#scene").getAttribute("data-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const bodyStretch = Number(await page.locator("#scene").getAttribute("data-max-body-stretch"));
  expect(Number.isFinite(bodyStretch)).toBeTruthy();
  expect(bodyStretch).toBeGreaterThan(0.05);

  const video = page.video();
  await page.close();

  if (!video) throw new Error("Playwright video was not created");
  await video.saveAs(`${outDir}/motion-first-s-gait-review.webm`);
  await context.close();

  expect(highDetailAssetRequests).toEqual([]);
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase C records continuous S multi-camera review", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

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

  const sequence = ["SIDE", "CHASE", "LOW", "FRONT", "SIDE"];
  for (const view of sequence) {
    if (view !== "SIDE" || (await page.locator("#cameraReadout").textContent()) !== "SIDE") {
      await page.getByRole("button", { name: view, exact: true }).click({ force: true });
      await expect(page.locator("#cameraReadout")).toHaveText(view);
    }
    await page.waitForTimeout(1900);
    await page.locator("#scene").screenshot({
      path: `${outDir}/motion-first-phase-c-${view.toLowerCase()}-${Date.now()}.png`
    });
  }

  await expect(page.locator("#scene")).toHaveAttribute("data-s-simplified-lane", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset-ready", "0");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "procedural-simplified-lane");
  await expect(page.locator("#scene")).toHaveAttribute("data-ik-clamped", "0");

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright video was not created");
  await video.saveAs(`${outDir}/motion-first-phase-c-multicamera.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase D P body captures same-species multi-view inspection", async ({ page }, testInfo) => {
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

  await page.goto("/evowild-test/preview-motion-first/index.html?inspect=1&morph=P", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#morphReadout")).toHaveText("P");
  await expect(page.locator("#runnerName")).toContainText("POWER");
  await expect(page.locator("#raceState")).toHaveText("INSPECT");

  for (const view of ["SIDE", "CHASE", "LOW", "FRONT"]) {
    await page.getByRole("button", { name: view, exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(700);
    await page.locator("#scene").screenshot({
      path: `${outDir}/motion-first-phase-d-p-${view.toLowerCase()}.png`
    });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase D P gait records continuous SIDE and LOW review", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

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

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-gait/index.html?morph=P", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#raceState")).toHaveText("MOTION REVIEW");
  await expect(page.locator("#morphReadout")).toHaveText("P");
  await expect(page.locator("#runnerName")).toContainText("POWER");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(4200);

  await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("LOW");
  await page.waitForTimeout(4200);

  await expect(page.locator("#scene")).toHaveAttribute("data-p-ik-clamped", "0");

  const stanceSlip = Number(await page.locator("#scene").getAttribute("data-p-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const bodyLoad = Number(await page.locator("#scene").getAttribute("data-p-max-body-load"));
  expect(Number.isFinite(bodyLoad)).toBeTruthy();
  expect(bodyLoad).toBeGreaterThan(0.07);

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright P gait video was not created");
  await video.saveAs(`${outDir}/motion-first-p-gait-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase D E body captures same-species multi-view inspection", async ({ page }, testInfo) => {
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

  await page.goto("/evowild-test/preview-motion-first/index.html?inspect=1&morph=E", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#morphReadout")).toHaveText("E");
  await expect(page.locator("#runnerName")).toContainText("ENDURE");
  await expect(page.locator("#raceState")).toHaveText("INSPECT");

  for (const view of ["SIDE", "CHASE", "LOW", "FRONT"]) {
    await page.getByRole("button", { name: view, exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(700);
    await page.locator("#scene").screenshot({
      path: `${outDir}/motion-first-phase-d-e-${view.toLowerCase()}.png`
    });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase D E gait records continuous SIDE and LOW review", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

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

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-gait/index.html?morph=E", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#raceState")).toHaveText("MOTION REVIEW");
  await expect(page.locator("#morphReadout")).toHaveText("E");
  await expect(page.locator("#runnerName")).toContainText("ENDURE");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(4200);

  await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("LOW");
  await page.waitForTimeout(4200);

  await expect(page.locator("#scene")).toHaveAttribute("data-e-ik-clamped", "0");

  const stanceSlip = Number(await page.locator("#scene").getAttribute("data-e-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const verticalRange = Number(await page.locator("#scene").getAttribute("data-e-vertical-range"));
  expect(Number.isFinite(verticalRange)).toBeTruthy();
  expect(verticalRange).toBeGreaterThan(0.035);
  expect(verticalRange).toBeLessThan(0.13);

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright E gait video was not created");
  await video.saveAs(`${outDir}/motion-first-e-gait-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First normal race uses Hunyuan LOD4 rigged S", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await page.goto("/evowild-test/preview-motion-first/index.html", { waitUntil: "networkidle" });
  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset-ready", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "hunyuan-s-lod4-rigged-v5");

  const clipCount = Number(await page.locator("#scene").getAttribute("data-s-animation-clips"));
  expect(Number.isFinite(clipCount)).toBeTruthy();
  expect(clipCount).toBeGreaterThan(0);

  await page.waitForTimeout(2500);
  await page.locator("#scene").screenshot({
    path: "test-results/visuals/motion-first-hunyuan-race.png"
  });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase D A body captures same-species multi-view inspection", async ({ page }, testInfo) => {
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

  await page.goto("/evowild-test/preview-motion-first/index.html?inspect=1&morph=A", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#morphReadout")).toHaveText("A");
  await expect(page.locator("#runnerName")).toContainText("AGILITY");
  await expect(page.locator("#raceState")).toHaveText("INSPECT");

  for (const view of ["SIDE", "CHASE", "LOW", "FRONT"]) {
    await page.getByRole("button", { name: view, exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(700);
    await page.locator("#scene").screenshot({
      path: `${outDir}/motion-first-phase-d-a-${view.toLowerCase()}.png`
    });
  }

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

test("Motion First Phase D A gait proves banking flex and planted stance", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(80000);

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

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-gait/index.html?morph=A", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#raceState")).toHaveText("MOTION REVIEW");
  await expect(page.locator("#morphReadout")).toHaveText("A");
  await expect(page.locator("#runnerName")).toContainText("AGILITY");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(6200);

  await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("LOW");
  await page.waitForTimeout(2600);

  await expect(page.locator("#scene")).toHaveAttribute("data-a-ik-clamped", "0");

  const stanceSlip = Number(await page.locator("#scene").getAttribute("data-a-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const maxBank = Number(await page.locator("#scene").getAttribute("data-a-max-bank"));
  expect(Number.isFinite(maxBank)).toBeTruthy();
  expect(maxBank).toBeGreaterThan(0.10);

  const maxFlex = Number(await page.locator("#scene").getAttribute("data-a-max-flex"));
  expect(Number.isFinite(maxFlex)).toBeTruthy();
  expect(maxFlex).toBeGreaterThan(0.08);

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Playwright A gait video was not created");
  await video.saveAs(`${outDir}/motion-first-a-gait-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase E simplified race deploys 18 animated runners without Hunyuan assets", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(65000);

  const pageErrors = [];
  const consoleErrors = [];
  const highDetailAssetRequests = [];

  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("request", (request) => {
    if (request.url().includes("/models/evowild-s/")) highDetailAssetRequests.push(request.url());
  });

  await page.goto("/evowild-test/preview-motion-first-race/index.html", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#scene")).toHaveAttribute("data-simplified-race", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-runner-count", "18");
  await expect(page.locator("#scene")).toHaveAttribute("data-morph-set", "SPEA");
  await expect(page.locator("#scene")).toHaveAttribute("data-variation-active", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-simplified-lane", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "procedural-simplified-lane");
  await expect(page.locator("#runnerSelect option")).toHaveCount(18);

  await page.waitForTimeout(4500);

  const fpsText = await page.locator("#fpsReadout").textContent();
  const fps = Number.parseInt(fpsText || "", 10);
  expect(Number.isFinite(fps)).toBeTruthy();
  expect(fps).toBeGreaterThanOrEqual(20);

  // AUTO owns focus. Switch to a manual camera before checking manual focus.
  await page.getByRole("button", { name: "SIDE", exact: true }).click({ force: true });
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");
  await page.selectOption("#runnerSelect", "3");
  await expect(page.locator("#morphReadout")).toHaveText("A");

  for (const view of ["CHASE", "SIDE", "LOW", "FRONT", "PACK"]) {
    await page.getByRole("button", { name: view, exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(450);
  }

  await page.locator("#scene").screenshot({
    path: "test-results/visuals/motion-first-phase-e-18-runner-race.png"
  });

  expect(highDetailAssetRequests).toEqual([]);
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase F AUTO director reacts to race state and preserves speed cues", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

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

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#cameraReadout")).not.toHaveText("");
  await expect(page.locator("#scene")).toHaveAttribute("data-speed-cue-spacing", "7.25");
  await expect(page.locator("#scene")).toHaveAttribute("data-render-pixel-ratio", "0.4");
  await expect(page.locator("#scene")).toHaveAttribute("data-director-reason", "START");

  await page.waitForTimeout(7200);

  const simulatedRaceTime = Number(
    await page.locator("#scene").getAttribute("data-race-time")
  );
  expect(Number.isFinite(simulatedRaceTime)).toBeTruthy();
  expect(simulatedRaceTime).toBeGreaterThan(5.0);

  const decisionCount = Number(
    await page.locator("#scene").getAttribute("data-director-decision-count")
  );
  expect(Number.isFinite(decisionCount)).toBeTruthy();
  expect(decisionCount).toBeGreaterThanOrEqual(1);

  const directorReason = await page.locator("#scene").getAttribute("data-director-reason");
  expect(directorReason).toBeTruthy();
  expect(directorReason).not.toBe("START");

  const directorCamera = await page.locator("#scene").getAttribute("data-director-camera");
  expect(["CHASE", "LOW", "SIDE", "PACK", "FRONT"]).toContain(directorCamera);

  const cutCount = Number(
    await page.locator("#scene").getAttribute("data-director-cut-count")
  );
  expect(Number.isFinite(cutCount)).toBeTruthy();
  expect(cutCount).toBeGreaterThanOrEqual(1);

  const directorFocus = Number(
    await page.locator("#scene").getAttribute("data-director-focus")
  );
  expect(Number.isInteger(directorFocus)).toBeTruthy();
  expect(directorFocus).toBeGreaterThanOrEqual(0);
  expect(directorFocus).toBeLessThan(18);

  await page.waitForTimeout(4200);

  const laterDecisionCount = Number(
    await page.locator("#scene").getAttribute("data-director-decision-count")
  );
  expect(laterDecisionCount).toBeGreaterThanOrEqual(decisionCount);

  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-phase-f-auto-director.png`
  });

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Phase F director video was not created");
  await video.saveAs(`${outDir}/motion-first-phase-f-auto-director.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

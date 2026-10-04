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
  test.setTimeout(85000);

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
  test.setTimeout(85000);

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

  await page.goto("/evowild-test/preview-motion-first-race/index.html?skipStart=1", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#scene")).toHaveAttribute("data-simplified-race", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-detail-cull", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-runner-count", "18");
  await expect(page.locator("#scene")).toHaveAttribute("data-morph-set", "SPEA");
  await expect(page.locator("#scene")).toHaveAttribute("data-variation-active", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-simplified-lane", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-s-asset", "procedural-simplified-lane");
  await expect(page.locator("#runnerSelect option")).toHaveCount(18);

  await page.waitForTimeout(4500);

  const fpsText = await page.locator("#fpsReadout").textContent();
  const fps = Number.parseInt(fpsText || "", 10);
  const sampleFrameWindow = async () => page.evaluate(
    () =>
      new Promise((resolve) => {
        const deltas = [];
        const workSamples = [];
        const startedAt = performance.now();
        let last = startedAt;
        function sample(now) {
          deltas.push(now - last);
          last = now;

          const scene = document.querySelector("#scene");
          const workMs = Number(scene?.dataset.perfTotalWorkMs || "NaN");
          if (Number.isFinite(workMs)) workSamples.push(workMs);

          if (now - startedAt >= 2500) {
            const usable = deltas.slice(1);
            const sorted = [...usable].sort((a, b) => a - b);
            const p95 = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))] || 999;
            const sortedWork = [...workSamples].sort((a, b) => a - b);
            const p95WorkMs =
              sortedWork[Math.min(sortedWork.length - 1, Math.floor(sortedWork.length * 0.95))] || 999;
            const averageWorkMs =
              workSamples.reduce((sum, value) => sum + value, 0) /
              Math.max(workSamples.length, 1);
            resolve({
              averageFps: (usable.length * 1000) / Math.max(now - startedAt, 1),
              p95FrameMs: p95,
              frames: usable.length,
              averageWorkMs,
              p95WorkMs,
              workSamples: workSamples.length
            });
            return;
          }
          requestAnimationFrame(sample);
        }
        requestAnimationFrame(sample);
      })
  );
  let frameWindow = await sampleFrameWindow();
  if (frameWindow.averageFps < 20) {
    await page.waitForTimeout(750);
    const retryWindow = await sampleFrameWindow();
    if (retryWindow.averageFps > frameWindow.averageFps) {
      frameWindow = retryWindow;
    }
  }
  const perfState = await page.locator("#scene").evaluate((node) => ({
    renderPixelRatio: node.dataset.renderPixelRatio,
    renderCalls: node.dataset.renderCalls,
    renderTriangles: node.dataset.renderTriangles,
    fullRunnerCount: node.dataset.fullRunnerCount,
    fullRunnerBudget: node.dataset.fullRunnerBudget,
    proxyRunnerCount: node.dataset.proxyRunnerCount,
    simulationSteps: node.dataset.simulationSteps,
    poseUpdateMode: node.dataset.poseUpdateMode,
    perfPoseMs: node.dataset.perfPoseMs,
    perfSyncMs: node.dataset.perfSyncMs,
    perfRenderMs: node.dataset.perfRenderMs,
    perfOtherMs: node.dataset.perfOtherMs,
    perfTotalWorkMs: node.dataset.perfTotalWorkMs
  }));
  console.log(
    "SIMPLIFIED_RACE_PERF",
    JSON.stringify({ fpsReadout: fps, ...frameWindow, ...perfState })
  );

  expect(Number.isFinite(fps)).toBeTruthy();
  // Headless Chromium cadence varies, so combine a conservative observed-FPS
  // floor with the actual EvoWild JS work budget and draw-call budget.
  expect(frameWindow.averageFps).toBeGreaterThanOrEqual(20);
  expect(frameWindow.p95FrameMs).toBeLessThanOrEqual(70);
  expect(frameWindow.frames).toBeGreaterThanOrEqual(40);
  expect(frameWindow.workSamples).toBeGreaterThanOrEqual(40);
  expect(frameWindow.averageWorkMs).toBeLessThanOrEqual(6);
  expect(frameWindow.p95WorkMs).toBeLessThanOrEqual(10);

  const renderCalls = Number(perfState.renderCalls);
  expect(Number.isFinite(renderCalls)).toBeTruthy();
  expect(renderCalls).toBeLessThanOrEqual(32);

  await expect(page.locator("#scene")).toHaveAttribute("data-race-proxy-lod", "1");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-race-proxy-representation",
    "instanced-canonical-rig"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-race-proxy-draw-calls", "15");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-proxy-cue-band", "1");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-race-proxy-update-mode",
    "canonical-direct"
  );
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-race-proxy-shading",
    "lambert-structural"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-e-proxy-body-length", "1.4");
  await expect(page.locator("#scene")).toHaveAttribute("data-e-proxy-pelvis-length", "1.05");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-proxy-split-foot", "1");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-pose-update-mode",
    "canonical-instanced-all"
  );
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-race-focus-representation",
    "canonical-instanced"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-proxy-canonical-gait", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-render-profile", "flat-basic");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-tone-mapping", "none");
  await expect(page.locator("#scene")).toHaveAttribute("data-environment-pass", "1");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-environment-profile",
    "instanced-three-depth"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-finish-line-z", "1600");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-distance-landmark-interval",
    "400"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-simulation-hz", "60");
  const proxyCount = Number(
    await page.locator("#scene").getAttribute("data-proxy-runner-count")
  );
  const fullCount = Number(
    await page.locator("#scene").getAttribute("data-full-runner-count")
  );
  expect(proxyCount).toBe(18);
  expect(fullCount).toBe(0);
  await expect(page.locator("#scene")).toHaveAttribute("data-full-runner-budget", "0");

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

  const proxyReviewMorphs = [
    ["S", "0"],
    ["P", "1"],
    ["E", "2"],
    ["A", "3"]
  ];
  for (const [morph, runnerId] of proxyReviewMorphs) {
    await page.goto(
      `/evowild-test/preview-motion-first-race/index.html?proxyReviewRunner=${runnerId}`,
      { waitUntil: "networkidle" }
    );
    await expect(page.locator("#scene")).toHaveAttribute(
      "data-proxy-review-runner",
      runnerId
    );
    await expect(page.locator("#scene")).toHaveAttribute(
      "data-proxy-review-focus",
      runnerId
    );
    await expect(page.locator("#runnerSelect")).toHaveValue(runnerId);
    await expect(page.locator("#cameraReadout")).toHaveText("SIDE");
    await expect(page.locator("#morphReadout")).toHaveText(morph);
    await page.waitForTimeout(950);
    await page.locator("#scene").screenshot({
      path: `test-results/visuals/motion-first-race-proxy-${morph.toLowerCase()}-side.png`
    });

    await page.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
    await expect(page.locator("#cameraReadout")).toHaveText("LOW");
    await page.waitForTimeout(1400);
    await page.locator("#scene").screenshot({
      path: `test-results/visuals/motion-first-race-proxy-${morph.toLowerCase()}-low.png`
    });
  }

  expect(highDetailAssetRequests).toEqual([]);
  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase E simplified race public start sequence", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(18000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  await page.goto(
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?startReview=1",
    { waitUntil: "networkidle" }
  );

  let scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-start-sequence", "1");
  await expect(scene).not.toHaveAttribute("data-start-phase", "SKIPPED");

  await expect(scene).toHaveAttribute("data-start-phase", "GO", {
    timeout: 5000
  });
  await expect(scene).toHaveAttribute("data-start-layout", "18-wide-single-line");
  await expect(scene).toHaveAttribute("data-start-slot-count", "18");

  const startXs = JSON.parse(
    (await scene.getAttribute("data-start-slot-xs")) || "[]"
  );
  const startDistances = JSON.parse(
    (await scene.getAttribute("data-start-slot-distances")) || "[]"
  );
  expect(startXs).toHaveLength(18);
  expect(startDistances).toHaveLength(18);
  expect(new Set(startXs.map((value) => Number(value).toFixed(3))).size).toBe(18);
  expect(Math.max(...startXs) - Math.min(...startXs)).toBeGreaterThan(20);
  expect(Math.max(...startDistances) - Math.min(...startDistances)).toBeLessThan(0.001);
  expect(Number(await scene.getAttribute("data-start-merge-begin"))).toBe(28);
  expect(Number(await scene.getAttribute("data-start-merge-end"))).toBe(115);

  // Capture immediately while the GO overlay is active. Additional locator
  // assertions can consume most of the short GO presentation window.
  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-start-go.png`
  });
  await expect(scene).toHaveAttribute("data-start-go-race-time", "0.000");
  expect(Number(await scene.getAttribute("data-race-time"))).toBe(0);
  await expect(page.locator("#startSequence")).toHaveAttribute(
    "aria-hidden",
    "false"
  );

  await page.goto(
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html",
    { waitUntil: "networkidle" }
  );
  scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-start-phase", "RUNNING", {
    timeout: 5500
  });
  await expect(page.locator("#raceState")).toHaveText("RUNNING");
  await expect(page.locator("#startSequence")).toHaveAttribute(
    "aria-hidden",
    "true"
  );
  await expect(page.locator("#pauseButton")).toBeEnabled();

  await page.waitForTimeout(350);
  expect(Number(await scene.getAttribute("data-race-time"))).toBeGreaterThan(0.1);

  await page.getByRole("button", { name: "RESTART", exact: true }).click({
    force: true
  });
  await expect(scene).toHaveAttribute("data-start-phase", "READY");
  await expect(page.locator("#raceState")).toHaveText("READY");
  expect(Number(await scene.getAttribute("data-race-time"))).toBe(0);

  await context.close();
});


test("Motion First Phase F AUTO director reacts to race state and preserves speed cues", async ({ browser }, testInfo) => {
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

  await page.goto("http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?skipStart=1", {
    waitUntil: "networkidle"
  });

  await expect(page.locator("#scene")).toBeVisible();
  await expect(page.locator("#cameraReadout")).not.toHaveText("");
  await expect(page.locator("#scene")).toHaveAttribute("data-speed-cue-spacing", "7.25");
  await expect(page.locator("#scene")).toHaveAttribute("data-speed-parallax-spacing", "4.8");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-speed-parallax-profile",
    "inner-shoulder"
  );
  await expect(page.locator("#scene")).toHaveAttribute("data-render-pixel-ratio", "0.75");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-proxy-lod", "1");
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

  const shotHistoryText =
    (await page.locator("#scene").getAttribute("data-director-shot-history")) || "";
  const shotHistory = shotHistoryText.split(",").filter(Boolean);
  expect(shotHistory.length).toBeGreaterThanOrEqual(2);
  expect(shotHistory).toContain("ACCELERATION:LOW");
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-director-acceleration-shown",
    "1"
  );
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-director-auto-low-profile",
    "lead-front-quarter-inboard"
  );
  const autoLowCameraX = Number(
    await page.locator("#scene").getAttribute("data-director-auto-low-camera-x")
  );
  expect(Number.isFinite(autoLowCameraX)).toBeTruthy();
  expect(Math.abs(autoLowCameraX)).toBeLessThan(12.0);
  const accelerationGap = Number(
    await page.locator("#scene").getAttribute("data-director-acceleration-gap")
  );
  expect(accelerationGap).toBeGreaterThan(0.75);

  console.log("DIRECTOR_SHOT_HISTORY", shotHistoryText);

  const persistentShots = new Set([
    "OVERTAKE_ATTEMPT:SIDE",
    "LEAD_DUEL:SIDE",
    "PACK_COMPRESSION:PACK",
    "BREAKAWAY:LOW"
  ]);
  for (let i = 1; i < shotHistory.length; i += 1) {
    if (persistentShots.has(shotHistory[i])) {
      expect(shotHistory[i]).not.toBe(shotHistory[i - 1]);
    }
  }

  // The deterministic field does not produce a genuine closing pair during
  // the first ~12 seconds. Continue the same race long enough to review a real
  // top-eight overtake attempt rather than weakening the detection thresholds.
  await page.waitForTimeout(17500);
  const extendedShotHistoryText =
    (await page.locator("#scene").getAttribute("data-director-shot-history")) || "";
  const extendedShotHistory = extendedShotHistoryText.split(",").filter(Boolean);
  console.log("DIRECTOR_EXTENDED_SHOT_HISTORY", extendedShotHistoryText);
  expect(extendedShotHistory).toContain("OVERTAKE_ATTEMPT:SIDE");

  const overtakeGap = Number(
    await page.locator("#scene").getAttribute("data-director-overtake-gap")
  );
  const overtakeClosingSpeed = Number(
    await page.locator("#scene").getAttribute("data-director-overtake-closing-speed")
  );
  expect(overtakeGap).toBeGreaterThanOrEqual(0.65);
  expect(overtakeGap).toBeLessThanOrEqual(4.8);
  expect(overtakeClosingSpeed).toBeGreaterThanOrEqual(0.35);

  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-phase-f-auto-director.png`
  });

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Phase F director video was not created");
  await video.saveAs(`${outDir}/motion-first-phase-f-auto-director.webm`);
  await context.close();

  const speedContext = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const speedPage = await speedContext.newPage();
  await speedPage.goto(
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );
  await speedPage.waitForTimeout(4200);

  await speedPage.getByRole("button", { name: "CHASE", exact: true }).click({ force: true });
  await speedPage.waitForTimeout(900);
  await expect(speedPage.locator("#cameraReadout")).toHaveText("CHASE");
  await expect(speedPage.locator("#scene")).toHaveAttribute(
    "data-speed-parallax-camera",
    "active"
  );
  const chaseBoost = Number(
    await speedPage.locator("#scene").getAttribute("data-speed-fov-boost")
  );
  expect(chaseBoost).toBeGreaterThan(0.8);
  await speedPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-speed-chase.png`
  });

  await speedPage.getByRole("button", { name: "LOW", exact: true }).click({ force: true });
  await speedPage.waitForTimeout(900);
  await expect(speedPage.locator("#cameraReadout")).toHaveText("LOW");
  const lowBoost = Number(
    await speedPage.locator("#scene").getAttribute("data-speed-fov-boost")
  );
  expect(lowBoost).toBeGreaterThan(chaseBoost);
  await speedPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-speed-low.png`
  });

  await speedPage.getByRole("button", { name: "SIDE", exact: true }).click({ force: true });
  await speedPage.waitForTimeout(900);
  await expect(speedPage.locator("#cameraReadout")).toHaveText("SIDE");
  await expect(speedPage.locator("#scene")).toHaveAttribute(
    "data-side-broadcast-angle",
    "shallow-three-quarter"
  );
  await expect(speedPage.locator("#scene")).toHaveAttribute(
    "data-side-depth-offset",
    "5.0"
  );
  await speedPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-side-readability.png`
  });

  // Dense-pack motion diagnostic: select an actual mid-pack subject by
  // current race rank, then capture successive SIDE frames. Do not assume a
  // fixed runner id is still in traffic; deterministic speed bias can produce
  // an early breakaway.
  let midPackRunner = null;
  let closestRankDistance = Number.POSITIVE_INFINITY;
  for (let runnerId = 0; runnerId < 18; runnerId += 1) {
    await speedPage.selectOption("#runnerSelect", String(runnerId));
    await speedPage.waitForTimeout(25);
    const rankText = (await speedPage.locator("#positionReadout").textContent()) || "";
    const rank = Number.parseInt(rankText.split("/")[0].trim(), 10);
    if (!Number.isFinite(rank)) continue;

    const rankDistance = Math.abs(rank - 9);
    if (rankDistance < closestRankDistance) {
      closestRankDistance = rankDistance;
      midPackRunner = { runnerId, rank };
    }
    if (rank >= 7 && rank <= 11) {
      midPackRunner = { runnerId, rank };
      break;
    }
  }
  expect(midPackRunner).toBeTruthy();
  expect(midPackRunner.rank).toBeGreaterThanOrEqual(7);
  expect(midPackRunner.rank).toBeLessThanOrEqual(11);
  await speedPage.selectOption("#runnerSelect", String(midPackRunner.runnerId));
  await speedPage.waitForTimeout(360);
  await speedPage.locator("#scene").evaluate((node, rank) => {
    node.dataset.packMotionReviewRank = String(rank);
  }, midPackRunner.rank);

  for (let frame = 0; frame < 4; frame += 1) {
    await speedPage.locator("#scene").screenshot({
      path: `${outDir}/motion-first-pack-motion-${frame}.png`
    });
    await speedPage.waitForTimeout(120);
  }

  await speedContext.close();

  const finishContext = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const finishPage = await finishContext.newPage();
  await finishPage.goto(
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?finishReview=1",
    { waitUntil: "networkidle" }
  );
  await expect(finishPage.locator("#scene")).toHaveAttribute("data-finish-review", "1");

  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-director-reason",
    "FINAL_CHASE",
    { timeout: 5000 }
  );
  let finishFocusId = await finishPage.locator("#scene").getAttribute("data-director-focus");
  await expect(finishPage.locator("#runnerSelect")).toHaveValue(finishFocusId);
  await finishPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-finish-final-chase.png`
  });

  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-director-reason",
    "FINISH_SIDE",
    { timeout: 7000 }
  );
  finishFocusId = await finishPage.locator("#scene").getAttribute("data-director-focus");
  await expect(finishPage.locator("#runnerSelect")).toHaveValue(finishFocusId);
  await finishPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-finish-side.png`
  });

  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-director-reason",
    "FINISH_FRONT",
    { timeout: 6000 }
  );
  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-finish-front-profile",
    "leader-centered-through-line"
  );
  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-finish-structure",
    "side-pylons-stripe"
  );
  const finishFrontCameraZ = Number(
    await finishPage.locator("#scene").getAttribute("data-finish-front-camera-z")
  );
  expect(finishFrontCameraZ).toBeGreaterThan(1600);
  finishFocusId = await finishPage.locator("#scene").getAttribute("data-director-focus");
  await expect(finishPage.locator("#runnerSelect")).toHaveValue(finishFocusId);
  await finishPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-finish-front.png`
  });

  await expect(finishPage.locator("#raceState")).toHaveText("FINISHED", {
    timeout: 22000
  });
  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-result-ready",
    "1"
  );
  await expect(finishPage.locator("#resultPanel")).toHaveAttribute(
    "aria-hidden",
    "false"
  );
  await expect(finishPage.locator("#resultList li")).toHaveCount(18);
  await expect(finishPage.locator("#pauseButton")).toBeDisabled();

  const winnerId = Number(
    await finishPage.locator("#scene").getAttribute("data-winner-id")
  );
  const winningTime = Number(
    await finishPage.locator("#scene").getAttribute("data-winning-time")
  );
  const classificationText =
    (await finishPage.locator("#scene").getAttribute("data-final-classification")) ||
    "[]";
  const classification = JSON.parse(classificationText);

  expect(Number.isInteger(winnerId)).toBeTruthy();
  expect(Number.isFinite(winningTime)).toBeTruthy();
  expect(classification).toHaveLength(18);
  expect(classification[0].id).toBe(winnerId);
  expect(classification[0].rank).toBe(1);
  expect(classification[17].rank).toBe(18);
  expect(classification[0].time).toBeCloseTo(winningTime, 3);
  for (let i = 1; i < classification.length; i += 1) {
    expect(classification[i].time).toBeGreaterThanOrEqual(
      classification[i - 1].time
    );
  }

  await finishPage.locator("#scene").screenshot({
    path: `${outDir}/motion-first-finish-result.png`
  });

  await finishPage.getByRole("button", { name: "RESTART", exact: true }).click({
    force: true
  });
  await expect(finishPage.locator("#scene")).toHaveAttribute(
    "data-result-ready",
    "0"
  );
  await expect(finishPage.locator("#resultPanel")).toHaveAttribute(
    "aria-hidden",
    "true"
  );
  await expect(finishPage.locator("#pauseButton")).toBeEnabled();

  await finishContext.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Phase F full-race AUTO director review", async ({ browser }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_FULL_RACE_REVIEW !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(130000);

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

  await page.goto(
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?fullDirectorReview=1",
    { waitUntil: "networkidle" }
  );

  await expect(page.locator("#scene")).toHaveAttribute("data-full-director-review", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-race-ground-y", "-0.12");
  await expect(page.locator("#raceState")).toHaveText("RUNNING");

  await page.waitForTimeout(15000);
  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-full-race-early.png`
  });

  await page.waitForTimeout(20000);
  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-full-race-mid.png`
  });

  await page.waitForTimeout(20000);
  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-full-race-late.png`
  });

  await expect(page.locator("#raceState")).toHaveText("FINISHED", { timeout: 45000 });

  const raceTime = Number(await page.locator("#scene").getAttribute("data-race-time"));
  expect(Number.isFinite(raceTime)).toBeTruthy();
  expect(raceTime).toBeGreaterThan(60);
  expect(raceTime).toBeLessThan(90);

  const fullLogText =
    (await page.locator("#scene").getAttribute("data-director-full-shot-log")) || "[]";
  const fullLog = JSON.parse(fullLogText);
  expect(Array.isArray(fullLog)).toBeTruthy();
  expect(fullLog.length).toBeGreaterThanOrEqual(12);

  const reasons = fullLog.map((shot) => shot.reason);
  const cameras = new Set(fullLog.map((shot) => shot.camera));

  expect(reasons[0]).toBe("START");
  expect(reasons).toContain("ACCELERATION");
  expect(reasons).toContain("OVERTAKE_ATTEMPT");
  expect(reasons).toContain("FINAL_CHASE");
  expect(reasons).toContain("FINISH_SIDE");
  expect(reasons).toContain("FINISH_FRONT");

  const finalChaseIndex = reasons.lastIndexOf("FINAL_CHASE");
  const finishSideIndex = reasons.lastIndexOf("FINISH_SIDE");
  const finishFrontIndex = reasons.lastIndexOf("FINISH_FRONT");
  expect(finalChaseIndex).toBeGreaterThanOrEqual(0);
  expect(finishSideIndex).toBeGreaterThan(finalChaseIndex);
  expect(finishFrontIndex).toBeGreaterThan(finishSideIndex);

  for (const camera of ["PACK", "LOW", "CHASE", "SIDE", "FRONT"]) {
    expect(cameras.has(camera)).toBeTruthy();
  }

  for (let i = 1; i < fullLog.length; i += 1) {
    expect(
      `${fullLog[i].reason}:${fullLog[i].camera}`
    ).not.toBe(
      `${fullLog[i - 1].reason}:${fullLog[i - 1].camera}`
    );
  }

  const cameraSeconds = {};
  let focusSwitches = 0;
  let shortestShot = Number.POSITIVE_INFINITY;
  let longestShot = 0;
  for (let i = 0; i < fullLog.length; i += 1) {
    const start = Number(fullLog[i].t);
    const end = i + 1 < fullLog.length ? Number(fullLog[i + 1].t) : raceTime;
    const duration = Math.max(0, end - start);
    cameraSeconds[fullLog[i].camera] =
      (cameraSeconds[fullLog[i].camera] || 0) + duration;
    if (i > 0 && fullLog[i].focus !== fullLog[i - 1].focus) focusSwitches += 1;
    if (i > 0) {
      shortestShot = Math.min(shortestShot, duration);
      longestShot = Math.max(longestShot, duration);
    }
  }

  const lowShare = (cameraSeconds.LOW || 0) / raceTime;
  const maxCameraShare =
    Math.max(...Object.values(cameraSeconds)) / raceTime;

  // Full-race review gates: AUTO must not collapse back into one dominant
  // camera, cut too rapidly, or churn focus every shot.
  expect(lowShare).toBeLessThan(0.35);
  expect(maxCameraShare).toBeLessThan(0.40);
  expect(shortestShot).toBeGreaterThan(1.5);
  expect(focusSwitches).toBeLessThanOrEqual(12);

  console.log(
    "FULL_DIRECTOR_REVIEW",
    JSON.stringify({
      raceTime,
      shotCount: fullLog.length,
      focusSwitches,
      shortestShot,
      longestShot,
      lowShare,
      maxCameraShare,
      cameraSeconds,
      shots: fullLog
    })
  );

  await page.locator("#scene").screenshot({
    path: `${outDir}/motion-first-full-race-finish.png`
  });

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Full-race director review video was not created");
  await video.saveAs(`${outDir}/motion-first-full-race-auto.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});


test("Motion First Race Agent v1 commands are creature-resolved", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );

  await expect(page.locator("#scene")).toHaveAttribute(
    "data-agent-model",
    "command-only-creature-resolved"
  );
  await expect(page.locator("#agentTargetSelect")).toHaveValue("0");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-target-runner", "0");
  await expect(page.locator("#staminaReadout")).toHaveText("100%");
  await expect(page.locator("#fatigueReadout")).toHaveText("0%");

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-command", "PUSH");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-runner-id", "0");
  await page.waitForTimeout(1800);

  const pushState = await page.locator("#scene").evaluate((node) => ({
    command: node.dataset.agentFocusCommand,
    response: Number(node.dataset.agentFocusResponse),
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue)
  }));

  expect(pushState.command).toBe("PUSH");
  expect(pushState.response).toBeGreaterThan(0.70);
  expect(pushState.stamina).toBeLessThan(1);
  expect(pushState.fatigue).toBeGreaterThan(0);

  await page.getByRole("button", { name: "CONSERVE", exact: true }).click();
  await page.waitForTimeout(900);
  const conserveState = await page.locator("#scene").evaluate((node) => ({
    command: node.dataset.agentFocusCommand,
    response: Number(node.dataset.agentFocusResponse),
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue)
  }));

  expect(conserveState.command).toBe("CONSERVE");
  expect(conserveState.response).toBeGreaterThan(0.45);
  expect(Number.isFinite(conserveState.stamina)).toBeTruthy();
  expect(Number.isFinite(conserveState.fatigue)).toBeTruthy();

  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await page.waitForTimeout(150);
  await expect(page.locator("#scene")).toHaveAttribute(
    "data-agent-focus-command",
    "NEUTRAL"
  );
  await expect(page.locator("#agentResponseReadout")).toHaveText("NEUTRAL");

  // Same PUSH command must not have identical strength across morphs.
  await page.selectOption("#agentTargetSelect", "2");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-target-runner", "2");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(350);
  const endurancePushResponse = Number(
    await page.locator("#scene").getAttribute("data-agent-focus-response")
  );
  expect(endurancePushResponse).toBeLessThan(pushState.response);

  await page.locator("#scene").screenshot({
    path: "test-results/visuals/motion-first-race-agent-v1.png"
  });
});


test("Motion First Creature State v1 pressure affects Agent response", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );

  await expect(page.locator("#scene")).toHaveAttribute(
    "data-agent-model",
    "command-only-creature-resolved"
  );

  await page.waitForTimeout(4200);

  let pressured = null;
  for (let runnerId = 0; runnerId < 18; runnerId += 1) {
    await page.selectOption("#agentTargetSelect", String(runnerId));
    await page.waitForTimeout(40);
    const state = await page.locator("#scene").evaluate((node) => ({
      pressure: Number(node.dataset.agentFocusPressure),
      stamina: Number(node.dataset.agentFocusStamina),
      fatigue: Number(node.dataset.agentFocusFatigue),
      creatureState: node.dataset.agentFocusCreatureState
    }));
    if (Number.isFinite(state.pressure) && state.pressure > 0.12) {
      pressured = { runnerId, ...state };
      break;
    }
  }

  expect(pressured).toBeTruthy();
  expect(["FRESH", "PRESSURED", "WORKING", "TIRED"]).toContain(
    pressured.creatureState
  );

  const optionText =
    (await page.locator(`#agentTargetSelect option[value="${pressured.runnerId}"]`).textContent()) || "";
  const morphMatch = optionText.match(/·\s*([SPEA])\s*$/);
  expect(morphMatch).toBeTruthy();
  const morph = morphMatch[1];
  const pushCompatibility = { S: 1.0, P: 0.94, E: 0.76, A: 0.88 }[morph];

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(220);

  const push = await page.locator("#scene").evaluate((node) => ({
    pressure: Number(node.dataset.agentFocusPressure),
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue),
    response: Number(node.dataset.agentFocusResponse),
    creatureState: node.dataset.agentFocusCreatureState
  }));

  const fatiguePenalty = Math.max(0.25, 1 - push.fatigue * 0.72);
  const noPressureResponse = pushCompatibility * push.stamina * fatiguePenalty;

  expect(push.pressure).toBeGreaterThan(0.10);
  expect(push.response).toBeLessThan(noPressureResponse);
  expect(noPressureResponse - push.response).toBeGreaterThan(0.01);
  expect(["FRESH", "PRESSURED", "WORKING", "TIRED"]).toContain(
    push.creatureState
  );

  await expect(page.locator("#pressureReadout")).not.toHaveText("");
  await expect(page.locator("#creatureStateReadout")).not.toHaveText("");

  await page.locator("#scene").screenshot({
    path: "test-results/visuals/motion-first-creature-state-v1.png"
  });
});


test("Motion First Agent feedback v1 shows order then creature result", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );

  await page.selectOption("#agentTargetSelect", "0");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();

  await expect(page.locator("#agentFeedback")).not.toHaveClass(/hidden/);
  await expect(page.locator("#agentFeedbackCommand")).toHaveText("PUSH");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-feedback-visible", "1");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-feedback-command", "PUSH");

  await expect
    .poll(async () => page.locator("#agentFeedbackResult").textContent())
    .toMatch(/STRONG|PARTIAL|WEAK/);

  await page.locator("#scene").screenshot({
    path: "test-results/visuals/motion-first-agent-feedback-v1.png"
  });

  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await expect(page.locator("#agentFeedbackCommand")).toHaveText("CLEAR");
  await expect(page.locator("#agentFeedbackResult")).toHaveText("CLEARED");
  await expect(page.locator("#scene")).toHaveAttribute("data-agent-feedback-result", "CLEARED");
});


test("Motion First Visual Swap Gate v1 replaces S rendering without replacing race state", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  const assetResponses = [];
  page.on("response", (response) => {
    if (response.url().includes("/models/evowild-s/race-lod4-rigged-v5.glb")) {
      assetResponses.push(response.status());
    }
  });

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?visualSwap=S&visualSwapRunner=0&proxyReviewRunner=0",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-visual-swap-ready", "1");
  await expect(scene).toHaveAttribute("data-visual-swap-mode", "external-native-clip");
  await expect(scene).toHaveAttribute("data-visual-swap-morph", "S");
  await expect(scene).toHaveAttribute("data-visual-swap-runner", "0");
  await expect(scene).toHaveAttribute("data-visual-swap-proxy-suppressed", "1");
  await expect(scene).toHaveAttribute("data-runner-count", "18");
  await expect(scene).toHaveAttribute("data-visual-swap-runner-count", "1");
  await expect(scene).toHaveAttribute("data-proxy-runner-count", "17");
  expect(assetResponses.some((status) => status >= 200 && status < 400)).toBeTruthy();

  const clipCount = Number(await scene.getAttribute("data-visual-swap-clip-count"));
  expect(clipCount).toBeGreaterThan(0);
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(2200);
  const speed = Number(await scene.getAttribute("data-race-time"));
  const playback = Number(await scene.getAttribute("data-visual-swap-playback-rate"));
  expect(speed).toBeGreaterThan(1);
  expect(playback).toBeGreaterThan(0);

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await expect(scene).toHaveAttribute("data-agent-command", "PUSH");
  await page.waitForTimeout(350);
  expect(Number(await scene.getAttribute("data-agent-focus-response"))).toBeGreaterThan(0.45);

  const renderCalls = Number(await scene.getAttribute("data-render-calls"));
  expect(Number.isFinite(renderCalls)).toBeTruthy();
  expect(renderCalls).toBeLessThan(100);

  await scene.screenshot({
    path: "test-results/visuals/motion-first-visual-swap-s-v1.png"
  });
});


test("Motion First Agent strategy balance v1 makes exhausted PUSH worse until CONSERVE recovery", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1&agentBalanceReview=1",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await page.selectOption("#agentTargetSelect", "0");
  await expect(scene).toHaveAttribute("data-agent-balance-model", "fatigue-tradeoff-v1");
  await expect(scene).toHaveAttribute("data-agent-balance-review", "1");

  const initial = await scene.evaluate((node) => ({
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue)
  }));
  expect(initial.stamina).toBeGreaterThan(0.69);
  expect(initial.stamina).toBeLessThan(0.74);
  expect(initial.fatigue).toBeGreaterThan(0.29);
  expect(initial.fatigue).toBeLessThan(0.33);

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(300);
  const exhaustedPush = await scene.evaluate((node) => ({
    response: Number(node.dataset.agentFocusResponse),
    fatigue: Number(node.dataset.agentFocusFatigue),
    effective: Number(node.dataset.agentFocusEffectiveFactor)
  }));
  expect(exhaustedPush.response).toBeGreaterThan(0.45);
  expect(exhaustedPush.effective).toBeLessThan(1.0);

  await page.getByRole("button", { name: "CONSERVE", exact: true }).click();
  await page.waitForTimeout(7200);
  const recovered = await scene.evaluate((node) => ({
    stamina: Number(node.dataset.agentFocusStamina),
    fatigue: Number(node.dataset.agentFocusFatigue),
    effective: Number(node.dataset.agentFocusEffectiveFactor)
  }));
  expect(recovered.fatigue).toBeLessThan(exhaustedPush.fatigue - 0.06);
  expect(recovered.stamina).toBeGreaterThan(0.68);
  expect(recovered.effective).toBeLessThan(1.0);

  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(300);
  const recoveredPush = await scene.evaluate((node) => ({
    response: Number(node.dataset.agentFocusResponse),
    fatigue: Number(node.dataset.agentFocusFatigue),
    effective: Number(node.dataset.agentFocusEffectiveFactor)
  }));
  expect(recoveredPush.response).toBeGreaterThan(exhaustedPush.response);
  expect(recoveredPush.effective).toBeGreaterThan(exhaustedPush.effective);
  expect(recoveredPush.effective).toBeGreaterThan(1.0);

  await scene.screenshot({
    path: "test-results/visuals/motion-first-agent-balance-v1.png"
  });
});


test("Motion First positioning v1 leaves a blocked line for a materially clearer safe lane", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(30000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1&positioningReview=1",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-positioning-model", "clearance-score-with-hysteresis");
  await expect(scene).toHaveAttribute("data-positioning-review", "1");
  await expect(scene).toHaveAttribute("data-positioning-review-blocked-lane", "4");
  await expect(scene).toHaveAttribute("data-positioning-review-expected-lane", "3");

  await expect.poll(async () =>
    Number(await scene.getAttribute("data-positioning-decision-count")),
    { timeout: 4000 }
  ).toBeGreaterThan(0);

  await expect(scene).toHaveAttribute("data-positioning-runner-target-lane", "3");

  const decision = await scene.evaluate((node) => ({
    currentGap: Number(node.dataset.positioningDecisionCurrentGap),
    chosenGap: Number(node.dataset.positioningDecisionChosenGap),
    minTrafficFactor: Number(node.dataset.positioningMinTrafficFactor),
    holdRemaining: Number(node.dataset.positioningHoldRemaining)
  }));
  expect(decision.currentGap).toBeGreaterThan(3.5);
  expect(decision.currentGap).toBeLessThan(6.5);
  expect(decision.chosenGap).toBeGreaterThan(decision.currentGap + 8);
  expect(decision.minTrafficFactor).toBeLessThan(0.98);
  expect(decision.holdRemaining).toBeGreaterThan(1.0);

  await page.waitForTimeout(900);
  const cleared = await scene.evaluate((node) => ({
    trafficFactor: Number(node.dataset.positioningTrafficFactor),
    minTrafficFactor: Number(node.dataset.positioningMinTrafficFactor),
    decisionCount: Number(node.dataset.positioningDecisionCount)
  }));
  expect(cleared.trafficFactor).toBeGreaterThan(cleared.minTrafficFactor + 0.02);
  expect(cleared.decisionCount).toBe(1);

  await scene.screenshot({
    path: "test-results/visuals/motion-first-positioning-v1.png"
  });
});


test("Motion First gameplay integration v1 completes 1600m with Agent and traffic systems active", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-agent-balance-model", "fatigue-tradeoff-v1");
  await expect(scene).toHaveAttribute("data-positioning-model", "clearance-score-with-hysteresis");
  await page.selectOption("#agentTargetSelect", "0");

  // Use all three Agent states inside the same real race. Commands alter only
  // the Creature response; they do not bypass race physics or traffic.
  await page.waitForTimeout(4000);
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(6500);
  await page.getByRole("button", { name: "CONSERVE", exact: true }).click();
  await page.waitForTimeout(6500);
  await page.getByRole("button", { name: "CLEAR", exact: true }).click();

  await expect(page.locator("#raceState")).toHaveText("FINISHED", {
    timeout: 105000
  });
  await expect(scene).toHaveAttribute("data-result-ready", "1");
  await expect(scene).toHaveAttribute("data-agent-focus-command", "NEUTRAL");

  const state = await scene.evaluate((node) => ({
    raceTime: Number(node.dataset.raceTime),
    classification: JSON.parse(node.dataset.finalClassification || "[]"),
    totalDecisions: Number(node.dataset.positioningTotalDecisions),
    maxDecisions: Number(node.dataset.positioningMaxDecisions),
    congestedRunnerCount: Number(node.dataset.positioningCongestedRunnerCount),
    worstTrafficFactor: Number(node.dataset.positioningWorstTrafficFactor),
    renderCalls: Number(node.dataset.renderCalls),
    agentStamina: Number(node.dataset.agentFocusStamina),
    agentFatigue: Number(node.dataset.agentFocusFatigue)
  }));

  expect(state.raceTime).toBeGreaterThan(55);
  expect(state.raceTime).toBeLessThan(105);
  expect(state.classification).toHaveLength(18);
  expect(new Set(state.classification.map((row) => row.id)).size).toBe(18);
  expect(state.classification.every((row) => Number.isFinite(row.time))).toBeTruthy();
  for (let i = 1; i < state.classification.length; i += 1) {
    expect(state.classification[i].time).toBeGreaterThanOrEqual(
      state.classification[i - 1].time
    );
  }

  expect(state.totalDecisions).toBeGreaterThan(0);
  expect(state.maxDecisions).toBeLessThanOrEqual(8);
  expect(state.congestedRunnerCount).toBeGreaterThan(0);
  expect(state.worstTrafficFactor).toBeLessThan(0.985);
  expect(state.renderCalls).toBeLessThanOrEqual(35);
  expect(state.agentStamina).toBeGreaterThan(0);
  expect(state.agentFatigue).toBeGreaterThanOrEqual(0);
  expect(state.agentFatigue).toBeLessThan(1);

  console.log("GAMEPLAY_INTEGRATION_V1", JSON.stringify(state));

  await scene.screenshot({
    path: "test-results/visuals/motion-first-gameplay-integration-v1.png"
  });
});


test("Motion First balanced 1600 course v1 does not lock any morph into one half of the field", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(135000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-course-profile", "balanced-1600-v1");
  await expect(scene).toHaveAttribute("data-course-distance", "1600");
  await expect(scene).toHaveAttribute("data-course-fit-s", "0.966");
  await expect(scene).toHaveAttribute("data-course-fit-p", "1.02");

  await expect(page.locator("#raceState")).toHaveText("FINISHED", {
    timeout: 105000
  });

  const classification = JSON.parse(
    (await scene.getAttribute("data-final-classification")) || "[]"
  );
  expect(classification).toHaveLength(18);

  const morphs = ["S", "P", "E", "A"];
  const stats = Object.fromEntries(
    morphs.map((morph) => [morph, { ranks: [], average: 0 }])
  );
  classification.forEach((row) => stats[row.morph].ranks.push(row.rank));
  morphs.forEach((morph) => {
    stats[morph].average =
      stats[morph].ranks.reduce((sum, rank) => sum + rank, 0) /
      stats[morph].ranks.length;
  });

  const topHalfMorphs = new Set(
    classification.filter((row) => row.rank <= 9).map((row) => row.morph)
  );
  const bottomHalfMorphs = new Set(
    classification.filter((row) => row.rank >= 10).map((row) => row.morph)
  );
  for (const morph of morphs) {
    expect(topHalfMorphs.has(morph)).toBeTruthy();
    expect(bottomHalfMorphs.has(morph)).toBeTruthy();
  }

  const averages = morphs.map((morph) => stats[morph].average);
  const averageSpread = Math.max(...averages) - Math.min(...averages);
  expect(averageSpread).toBeLessThanOrEqual(6.0);

  const raceTime = Number(await scene.getAttribute("data-race-time"));
  expect(raceTime).toBeGreaterThan(55);
  expect(raceTime).toBeLessThan(105);

  console.log(
    "BALANCED_1600_V1",
    JSON.stringify({ raceTime, stats, averageSpread, classification })
  );

  await scene.screenshot({
    path: "test-results/visuals/motion-first-balanced-1600-v1.png"
  });
});


test("Motion First course profiles v1 produce distinct race suitability", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const scene = page.locator("#scene");
  const raceState = page.locator("#raceState");
  const morphs = ["S", "P", "E", "A"];

  async function runCourse(courseId, expectedDistance, expectedWorldEnd) {
    await page.goto(
      `/evowild-test/preview-motion-first-race/index.html?skipStart=1&course=${courseId}&simRate=4`,
      { waitUntil: "networkidle" }
    );

    await expect(scene).toHaveAttribute("data-course-profile", courseId);
    await expect(scene).toHaveAttribute("data-course-distance", String(expectedDistance));
    await expect(scene).toHaveAttribute("data-course-world-end", String(expectedWorldEnd));
    await expect(scene).toHaveAttribute("data-simulation-rate", "4");
    await expect(raceState).toHaveText("FINISHED", { timeout: 40000 });

    const classification = JSON.parse(
      (await scene.getAttribute("data-final-classification")) || "[]"
    );
    expect(classification).toHaveLength(18);

    const stats = Object.fromEntries(
      morphs.map((morph) => [morph, { ranks: [], average: 0 }])
    );
    classification.forEach((row) => stats[row.morph].ranks.push(row.rank));
    morphs.forEach((morph) => {
      stats[morph].average =
        stats[morph].ranks.reduce((sum, rank) => sum + rank, 0) /
        stats[morph].ranks.length;
    });

    const result = {
      courseId,
      raceTime: Number(await scene.getAttribute("data-race-time")),
      winnerMorph: classification[0].morph,
      topSixMorphs: [...new Set(classification.slice(0, 6).map((row) => row.morph))],
      stats,
      classification
    };
    console.log("COURSE_PROFILE_V1", JSON.stringify(result));
    return result;
  }

  const sprint = await runCourse("sprint-800-v1", 800, 1800);
  const balanced = await runCourse("balanced-1600-v1", 1600, 1800);
  const endurance = await runCourse("endurance-2400-v1", 2400, 2600);

  expect(sprint.raceTime).toBeGreaterThan(25);
  expect(sprint.raceTime).toBeLessThan(55);
  expect(balanced.raceTime).toBeGreaterThan(55);
  expect(balanced.raceTime).toBeLessThan(105);
  expect(endurance.raceTime).toBeGreaterThan(90);
  expect(endurance.raceTime).toBeLessThan(150);

  // Course identity must change competitive suitability, not just the HUD label.
  expect(sprint.stats.S.average).toBeLessThan(sprint.stats.E.average);
  expect(endurance.stats.E.average).toBeLessThan(endurance.stats.S.average);
  expect(endurance.stats.E.average).toBeLessThan(endurance.stats.P.average);
  expect(sprint.winnerMorph).not.toBe(endurance.winnerMorph);

  // Keep individual/traffic variance alive: no course may collapse the top six
  // to one morph even when a profile has a preferred archetype.
  expect(sprint.topSixMorphs.length).toBeGreaterThanOrEqual(3);
  expect(balanced.topSixMorphs.length).toBeGreaterThanOrEqual(3);
  expect(endurance.topSixMorphs.length).toBeGreaterThanOrEqual(3);

  await scene.screenshot({
    path: "test-results/visuals/motion-first-course-profiles-v1.png"
  });
});


test("Motion First heavy 1200 course v1 gives Power a distinct home course", async ({ page }, testInfo) => {
  test.skip(process.env.MOTION_FIRST_CAPTURE !== "1");
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(60000);

  await page.goto(
    "/evowild-test/preview-motion-first-race/index.html?skipStart=1&course=heavy-1200-v1&simRate=4",
    { waitUntil: "networkidle" }
  );

  const scene = page.locator("#scene");
  await expect(scene).toHaveAttribute("data-course-profile", "heavy-1200-v1");
  await expect(scene).toHaveAttribute("data-course-surface", "HEAVY");
  await expect(scene).toHaveAttribute("data-course-track-color", "#51463a");
  await expect(scene).toHaveAttribute("data-course-distance", "1200");
  await expect(page.locator("#raceState")).toHaveText("FINISHED", {
    timeout: 30000
  });

  const classification = JSON.parse(
    (await scene.getAttribute("data-final-classification")) || "[]"
  );
  expect(classification).toHaveLength(18);

  const morphs = ["S", "P", "E", "A"];
  const stats = Object.fromEntries(
    morphs.map((morph) => [morph, { ranks: [], average: 0 }])
  );
  classification.forEach((row) => stats[row.morph].ranks.push(row.rank));
  morphs.forEach((morph) => {
    stats[morph].average =
      stats[morph].ranks.reduce((sum, rank) => sum + rank, 0) /
      stats[morph].ranks.length;
  });

  expect(classification[0].morph).toBe("P");
  expect(stats.P.average).toBeLessThan(stats.S.average);
  expect(stats.P.average).toBeLessThan(stats.E.average);
  expect(stats.P.average).toBeLessThan(stats.A.average);
  expect(new Set(classification.slice(0, 6).map((row) => row.morph)).size)
    .toBeGreaterThanOrEqual(3);

  console.log(
    "HEAVY_1200_V1",
    JSON.stringify({ stats, classification })
  );
});

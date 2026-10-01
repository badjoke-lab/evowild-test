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
  const frameWindow = await page.evaluate(
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
    "http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html",
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

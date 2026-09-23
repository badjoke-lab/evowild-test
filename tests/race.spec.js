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
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 12000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-profile", "s-sf3d-corrected-candidate", { timeout: 12000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-triangles", "8960", { timeout: 12000 });
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


test("benchmark Stable Fast 3D scaling at 1 4 and 18 instances", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const count of [1, 4, 18]) {
    await page.goto(`/evowild-test/?sf3dBench=${count}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 12000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 30000 });

    const metrics = await page.evaluate(() => window.__sf3dBench);
    expect(metrics?.count).toBe(count);
    expect(metrics?.trianglesPerInstance).toBeGreaterThan(0);
    expect(metrics?.rendererTriangles).toBeGreaterThan(0);
    expect(metrics?.rendererCalls).toBeGreaterThan(0);

    results.push(metrics);
    console.log("SF3D_BENCH", JSON.stringify(metrics));
    await page.locator("#stage").screenshot({ path: `${outDir}/sf3d-bench-${count}.png` });
  }

  fs.writeFileSync(
    `${outDir}/sf3d-benchmark.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare 18-instance SF3D double-side versus front-side rendering", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const results = [];
  for (const side of ["double", "front"]) {
    await page.goto(`/evowild-test/?sf3dBench=18&sf3dSide=${side}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 12000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench-side", side, { timeout: 12000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 30000 });

    const metrics = await page.evaluate(() => window.__sf3dBench);
    expect(metrics?.count).toBe(18);
    expect(metrics?.materialSide).toBe(side);
    results.push(metrics);
    console.log("SF3D_SIDE_BENCH", JSON.stringify(metrics));
  }

  fs.mkdirSync("test-results/visuals", { recursive: true });
  fs.writeFileSync(
    "test-results/visuals/sf3d-side-benchmark.json",
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare 18-instance SF3D clone versus instanced rendering", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const mode of ["clone", "instance"]) {
    await page.goto(`/evowild-test/?sf3dBench=18&sf3dMode=${mode}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 12000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench-mode", mode, { timeout: 12000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 30000 });

    const metrics = await page.evaluate(() => window.__sf3dBench);
    expect(metrics?.count).toBe(18);
    expect(metrics?.mode).toBe(mode);
    expect(metrics?.supported).toBe(true);
    expect(metrics?.rendererTriangles).toBeGreaterThan(0);
    expect(metrics?.rendererCalls).toBeGreaterThan(0);
    results.push(metrics);
    console.log("SF3D_MODE_BENCH", JSON.stringify(metrics));

    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-mode-${mode}-18.png`
    });
  }

  const cloneResult = results.find((result) => result.mode === "clone");
  const instanceResult = results.find((result) => result.mode === "instance");
  expect(instanceResult.rendererCalls).toBeLessThan(cloneResult.rendererCalls);

  fs.writeFileSync(
    `${outDir}/sf3d-mode-benchmark.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare five 3D creature generation candidates", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const variants = [
    {
      name: "corrected",
      query: "",
      profile: "s-sf3d-corrected-candidate",
      triangles: "8960"
    },
    {
      name: "white",
      query: "?sf3dVariant=white",
      profile: "s-sf3d-crop30-white",
      triangles: "9480"
    },
    {
      name: "side",
      query: "?sf3dVariant=side",
      profile: "s-sf3d-side-authority",
      triangles: "16112"
    },
    {
      name: "triposr-side",
      query: "?sf3dVariant=triposr",
      profile: "s-triposr-side-authority",
      triangles: "12764"
    },
    {
      name: "triposr-3q",
      query: "?sf3dVariant=triposr3q",
      profile: "s-triposr-3q-crop30",
      triangles: "15024"
    }
  ];

  const results = [];
  for (const variant of variants) {
    await page.goto(`/evowild-test/${variant.query}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-profile", variant.profile, { timeout: 15000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-triangles", variant.triangles, { timeout: 15000 });

    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(800);

    const stats = await page.locator("#stage").evaluate((stage) => ({
      profile: stage.dataset.sf3dProfile,
      triangles: Number(stage.dataset.sf3dTriangles),
      meshes: Number(stage.dataset.sf3dMeshes),
      materials: Number(stage.dataset.sf3dMaterials),
      textures: Number(stage.dataset.sf3dTextures),
      animations: Number(stage.dataset.sf3dAnimations),
      bounds: stage.dataset.sf3dBounds
    }));

    results.push({ name: variant.name, ...stats });
    console.log("SF3D_VARIANT", JSON.stringify({ name: variant.name, ...stats }));
    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-variant-${variant.name}.png`
    });
  }

  fs.writeFileSync(
    `${outDir}/sf3d-variant-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});

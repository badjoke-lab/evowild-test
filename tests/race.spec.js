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


test("compare corrected SF3D LOD quality and 18-instance load", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const variants = [
    { name: "base", query: "" },
    { name: "lod1", query: "?sf3dVariant=lod1" },
    { name: "lod2", query: "?sf3dVariant=lod2" },
    { name: "lod3", query: "?sf3dVariant=lod3" }
  ];

  const results = [];

  for (const variant of variants) {
    await page.goto(`/evowild-test/${variant.query}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });

    const modelStats = await page.locator("#stage").evaluate((stage) => ({
      profile: stage.dataset.sf3dProfile,
      triangles: Number(stage.dataset.sf3dTriangles),
      meshes: Number(stage.dataset.sf3dMeshes),
      materials: Number(stage.dataset.sf3dMaterials),
      textures: Number(stage.dataset.sf3dTextures),
      bounds: stage.dataset.sf3dBounds
    }));

    expect(modelStats.triangles).toBeGreaterThan(0);
    expect(modelStats.meshes).toBe(1);
    expect(modelStats.materials).toBeGreaterThan(0);
    expect(modelStats.textures).toBeGreaterThanOrEqual(2);

    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(700);
    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-lod-${variant.name}.png`
    });

    const benchJoin = variant.query ? "&" : "?";
    await page.goto(
      `/evowild-test/${variant.query}${benchJoin}sf3dBench=18&sf3dMode=clone&sf3dSide=front`,
      { waitUntil: "networkidle" }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 35000 });
    const bench = await page.evaluate(() => window.__sf3dBench);
    expect(bench?.count).toBe(18);
    expect(bench?.rendererTriangles).toBeGreaterThan(0);

    const result = { name: variant.name, ...modelStats, bench };
    results.push(result);
    console.log("SF3D_LOD_BENCH", JSON.stringify(result));
  }

  expect(results[1].triangles).toBeLessThan(results[0].triangles);
  expect(results[2].triangles).toBeLessThan(results[1].triangles);
  expect(results[3].triangles).toBeLessThan(results[2].triangles);

  fs.writeFileSync(
    `${outDir}/sf3d-lod-benchmark.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("loads four-level SF3D race LOD on the active corrected candidate", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod", "loaded", { timeout: 20000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod-levels", "4");
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod-distances", "0,9,18,30");

  const lod = await page.evaluate(() => ({
    levels: window.__sf3dRaceLod?.levels?.length || 0,
    distances: window.__sf3dRaceLod?.levels?.map((level) => level.distance) || []
  }));

  expect(lod.levels).toBe(4);
  expect(lod.distances).toEqual([0, 9, 18, 30]);

  await page.getByRole("button", { name: "2 Race" }).click();
  await page.waitForTimeout(900);
  await page.locator("#stage").screenshot({ path: `${outDir}/sf3d-race-lod-proof.png` });
});


test("benchmark mixed-distance 18-racer SF3D LOD", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/?sf3dRaceLodBench=1", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod-bench", "ready", { timeout: 30000 });

  const metrics = await page.evaluate(() => window.__sf3dRaceLodBench);
  expect(metrics?.count).toBe(18);
  expect(metrics?.rendererTriangles).toBeGreaterThan(0);
  expect(metrics?.rendererTriangles).toBeLessThan(metrics?.allBaseTriangles + 10);
  expect(metrics?.rendererCalls).toBeGreaterThan(0);

  console.log("SF3D_RACE_LOD_BENCH", JSON.stringify(metrics));
  fs.writeFileSync(
    `${outDir}/sf3d-race-lod-benchmark.json`,
    JSON.stringify(metrics, null, 2)
  );
  await page.locator("#stage").screenshot({
    path: `${outDir}/sf3d-race-lod-benchmark.png`
  });
});


test("compare moving 18-racer four-level LOD clone versus dynamic instancing", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const mode of ["clone", "instance"]) {
    await page.goto(
      `/evowild-test/?sf3dRaceStress=1&sf3dRaceStressMode=${mode}`,
      { waitUntil: "networkidle" }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress-racers", "18", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress-mode", mode, { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress", "ready", { timeout: 40000 });

    const metrics = await page.evaluate(() => window.__sf3dRaceStress);
    expect(metrics?.racers).toBe(18);
    expect(metrics?.mode).toBe(mode);
    expect(metrics?.samples).toBeGreaterThan(10);
    expect(metrics?.averageRendererTriangles).toBeGreaterThan(0);
    expect(metrics?.averageRendererTriangles).toBeLessThan(metrics?.allBaseTriangles);
    expect(metrics?.maxRendererCalls).toBeGreaterThan(0);

    results.push(metrics);
    console.log("SF3D_RACE_STRESS", JSON.stringify(metrics));
    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-race-stress-${mode}.png`
    });
  }

  const cloneResult = results.find((result) => result.mode === "clone");
  const instanceResult = results.find((result) => result.mode === "instance");
  expect(instanceResult.averageRendererCalls).toBeLessThan(cloneResult.averageRendererCalls);

  fs.writeFileSync(
    `${outDir}/sf3d-race-stress-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare render scale in dynamic-instanced 18-racer stress", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(140000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const scale of [1, 0.75, 0.5]) {
    await page.goto(
      `/evowild-test/?sf3dRaceStress=1&sf3dRaceStressMode=instance&renderScale=${scale}`,
      { waitUntil: "networkidle" }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress-mode", "instance", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-render-scale", String(scale), { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress", "ready", { timeout: 40000 });

    const metrics = await page.evaluate(() => window.__sf3dRaceStress);
    expect(metrics?.mode).toBe("instance");
    expect(metrics?.renderScale).toBe(scale);
    expect(metrics?.samples).toBeGreaterThan(10);
    results.push(metrics);
    console.log("SF3D_RENDER_SCALE", JSON.stringify(metrics));

    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-render-scale-${String(scale).replace(".", "_")}.png`
    });
  }

  fs.writeFileSync(
    `${outDir}/sf3d-render-scale-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare full versus lite far-LOD materials at render scale 0.75", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const materialMode of ["full", "lite"]) {
    await page.goto(
      `/evowild-test/?sf3dRaceStress=1&sf3dRaceStressMode=instance&renderScale=0.75&sf3dMaterialMode=${materialMode}`,
      { waitUntil: "networkidle" }
    );

    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress-mode", "instance", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-material-mode", materialMode, { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress", "ready", { timeout: 40000 });

    const metrics = await page.evaluate(() => window.__sf3dRaceStress);
    expect(metrics?.mode).toBe("instance");
    expect(metrics?.materialMode).toBe(materialMode);
    expect(metrics?.renderScale).toBe(0.75);
    expect(metrics?.samples).toBeGreaterThan(10);

    results.push(metrics);
    console.log("SF3D_MATERIAL_MODE", JSON.stringify(metrics));

    await page.locator("#stage").screenshot({
      path: `${outDir}/sf3d-material-${materialMode}.png`
    });
  }

  fs.writeFileSync(
    `${outDir}/sf3d-material-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("capture fixed LOD2 and LOD3 full versus lite material previews", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  for (const lod of ["lod2", "lod3"]) {
    for (const materialMode of ["full", "lite"]) {
      await page.goto(
        `/evowild-test/?sf3dVariant=${lod}&sf3dMaterialMode=${materialMode}`,
        { waitUntil: "networkidle" }
      );
      await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });
      await page.getByRole("button", { name: "1 Morph" }).click();
      await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
      await page.waitForTimeout(900);
      await page.locator("#stage").screenshot({
        path: `${outDir}/sf3d-${lod}-material-${materialMode}.png`
      });
    }
  }
});

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

  expect(results).toHaveLength(4);
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


test("physical lite LOD2 and LOD3 assets prune the normal texture", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const results = [];
  for (const variant of ["lod2", "lod2lite", "lod3", "lod3lite"]) {
    await page.goto(`/evowild-test/?sf3dVariant=${variant}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 15000 });

    const stats = await page.locator("#stage").evaluate((stage) => ({
      profile: stage.dataset.sf3dProfile,
      triangles: Number(stage.dataset.sf3dTriangles),
      textures: Number(stage.dataset.sf3dTextures)
    }));
    results.push({ variant, ...stats });
    console.log("SF3D_PHYSICAL_LITE", JSON.stringify({ variant, ...stats }));
  }

  const byName = Object.fromEntries(results.map((result) => [result.variant, result]));
  expect(byName.lod2lite.triangles).toBe(byName.lod2.triangles);
  expect(byName.lod3lite.triangles).toBe(byName.lod3.triangles);
  expect(byName.lod2lite.textures).toBeLessThan(byName.lod2.textures);
  expect(byName.lod3lite.textures).toBeLessThan(byName.lod3.textures);
});


test("compare Hunyuan multiview raw shape against active SF3D candidate", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const variants = [
    { name: "sf3d", query: "", profile: "s-sf3d-corrected-candidate" },
    { name: "hunyuan2mv", query: "?sf3dVariant=hunyuan2mv", profile: "s-hunyuan2mv-raw" }
  ];

  const results = [];
  for (const variant of variants) {
    await page.goto(`/evowild-test/${variant.query}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 30000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-profile", variant.profile, { timeout: 30000 });

    const stats = await page.locator("#stage").evaluate((stage) => ({
      profile: stage.dataset.sf3dProfile,
      triangles: Number(stage.dataset.sf3dTriangles),
      meshes: Number(stage.dataset.sf3dMeshes),
      textures: Number(stage.dataset.sf3dTextures),
      bounds: stage.dataset.sf3dBounds
    }));
    results.push({ name: variant.name, ...stats });
    console.log("MULTIVIEW_SHAPE_COMPARE", JSON.stringify({ name: variant.name, ...stats }));

    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(1200);
    await page.locator("#stage").screenshot({
      path: `${outDir}/shape-compare-${variant.name}.png`
    });
  }

  expect(results[1].triangles).toBeGreaterThan(results[0].triangles);
  fs.writeFileSync(
    `${outDir}/multiview-shape-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("capture four-view comparison for Hunyuan SF3D and TripoSR", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const candidates = [
    { name: "hunyuan2mv", variant: "hunyuan2mv" },
    { name: "sf3d-corrected", variant: "" },
    { name: "triposr-3q", variant: "triposr3q" }
  ];
  const yaws = [0, 90, 180, 270];

  for (const candidate of candidates) {
    for (const yaw of yaws) {
      const params = new URLSearchParams();
      if (candidate.variant) params.set("sf3dVariant", candidate.variant);
      params.set("modelYaw", String(yaw));
      await page.goto(`/evowild-test/?${params.toString()}`, { waitUntil: "domcontentloaded", timeout: 30000 });

      await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
      await expect(page.locator("#stage")).toHaveAttribute("data-model-yaw", String(yaw), { timeout: 20000 });
      await page.getByRole("button", { name: "1 Morph" }).click();
      await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
      await page.waitForTimeout(500);

      await page.locator("#stage").screenshot({
        path: `${outDir}/shape4-${candidate.name}-yaw${yaw}.png`
      });
    }
  }
});


test("compare raw and simplified Hunyuan multiview shapes", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const variants = [
    { name: "raw", query: "?sf3dVariant=hunyuan2mv" },
    { name: "clean", query: "?sf3dVariant=hunyuanclean" },
    { name: "lod1", query: "?sf3dVariant=hunyuanlod1" },
    { name: "lod2", query: "?sf3dVariant=hunyuanlod2" },
    { name: "lod3", query: "?sf3dVariant=hunyuanlod3" },
    { name: "lod4", query: "?sf3dVariant=hunyuanlod4" }
  ];
  const results = [];

  for (const variant of variants) {
    await page.goto(`/evowild-test/${variant.query}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });

    const stats = await page.locator("#stage").evaluate((stage) => ({
      profile: stage.dataset.sf3dProfile,
      triangles: Number(stage.dataset.sf3dTriangles),
      meshes: Number(stage.dataset.sf3dMeshes),
      bounds: stage.dataset.sf3dBounds
    }));
    expect(stats.triangles).toBeGreaterThan(0);
    results.push({ name: variant.name, ...stats });
    console.log("HUNYUAN_SIMPLIFY", JSON.stringify({ name: variant.name, ...stats }));

    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(500);
    await page.locator("#stage").screenshot({
      path: `${outDir}/hunyuan-${variant.name}.png`
    });
  }

  expect(results[1].triangles).toBeLessThan(results[0].triangles);
  expect(results[2].triangles).toBeLessThan(results[1].triangles);

  fs.writeFileSync(
    `${outDir}/hunyuan-simplify-comparison.json`,
    JSON.stringify({ generatedBy: "Playwright CI Chromium", results }, null, 2)
  );
});


test("compare Hunyuan raw and LOD2 across four views", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(180000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const variants = [
    { name: "raw", variant: "hunyuan2mv" },
    { name: "lod2", variant: "hunyuanlod2" }
  ];
  const yaws = [0, 90, 180, 270];

  for (const variant of variants) {
    for (const yaw of yaws) {
      const params = new URLSearchParams({
        sf3dVariant: variant.variant,
        modelYaw: String(yaw)
      });
      await page.goto(`/evowild-test/?${params.toString()}`, { waitUntil: "networkidle" });
      await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
      await expect(page.locator("#stage")).toHaveAttribute("data-model-yaw", String(yaw), { timeout: 20000 });
      await page.getByRole("button", { name: "1 Morph" }).click();
      await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
      await page.waitForTimeout(350);
      await page.locator("#stage").screenshot({
        path: `${outDir}/hunyuan4-${variant.name}-yaw${yaw}.png`
      });
    }
  }
});


test("benchmark 18 Hunyuan LOD2 instances", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanlod2&sf3dBench=18&sf3dMode=instance&sf3dSide=double&renderScale=0.75",
    { waitUntil: "networkidle" }
  );
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 35000 });

  const metrics = await page.evaluate(() => window.__sf3dBench);
  expect(metrics?.count).toBe(18);
  expect(metrics?.mode).toBe("instance");
  expect(metrics?.trianglesPerInstance).toBeGreaterThan(10000);
  expect(metrics?.rendererTriangles).toBeGreaterThan(200000);

  console.log("HUNYUAN_18_BENCH", JSON.stringify(metrics));
  fs.writeFileSync(
    `${outDir}/hunyuan-lod2-18-benchmark.json`,
    JSON.stringify(metrics, null, 2)
  );
  await page.locator("#stage").screenshot({
    path: `${outDir}/hunyuan-lod2-18-benchmark.png`
  });
});


test("benchmark 18 Hunyuan LOD3 and LOD4 instances", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  for (const variant of [
    { name: "lod3", query: "hunyuanlod3" },
    { name: "lod4", query: "hunyuanlod4" }
  ]) {
    await page.goto(
      `/evowild-test/?sf3dVariant=${variant.query}&sf3dBench=18&sf3dMode=instance&sf3dSide=double&renderScale=0.75`,
      { waitUntil: "networkidle" }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-bench", "ready", { timeout: 35000 });

    const metrics = await page.evaluate(() => window.__sf3dBench);
    expect(metrics?.count).toBe(18);
    expect(metrics?.mode).toBe("instance");
    expect(metrics?.trianglesPerInstance).toBeGreaterThan(0);
    results.push({ name: variant.name, ...metrics });
    console.log("HUNYUAN_LOD_18_BENCH", JSON.stringify({ name: variant.name, ...metrics }));

    await page.locator("#stage").screenshot({
      path: `${outDir}/hunyuan-${variant.name}-18-benchmark.png`
    });
  }

  expect(results[1].trianglesPerInstance).toBeLessThan(results[0].trianglesPerInstance);
  fs.writeFileSync(
    `${outDir}/hunyuan-lod3-lod4-18-benchmark.json`,
    JSON.stringify(results, null, 2)
  );
});


test("compare SF3D TripoSR and semantic Hunyuan across four views", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  const candidates = [
    { name: "sf3d", variant: "" },
    { name: "triposr", variant: "triposr3q" },
    { name: "hunyuan", variant: "hunyuanlod2" }
  ];
  const yaws = [0, 90, 180, 270];

  for (const candidate of candidates) {
    for (const yaw of yaws) {
      const params = new URLSearchParams({ modelYaw: String(yaw) });
      if (candidate.variant) params.set("sf3dVariant", candidate.variant);
      await page.goto(`/evowild-test/?${params.toString()}`, { waitUntil: "networkidle" });
      await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
      await page.getByRole("button", { name: "1 Morph" }).click();
      await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
      await page.waitForTimeout(350);
      await page.locator("#stage").screenshot({
        path: `${outDir}/direct3d-${candidate.name}-yaw${yaw}.png`
      });
    }
  }
});


test("capture styled Hunyuan prototype in Morph Lab and Race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  for (const yaw of [0, 90, 180, 270]) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&modelYaw=${yaw}`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-profile", "s-hunyuan2mv-styled-prototype");
    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(450);
    await page.locator("#stage").screenshot({
      path: `${outDir}/hunyuan-styled-yaw${yaw}.png`
    });
  }

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanstyled&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod", "loaded", { timeout: 25000 });
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod-levels", "3");
  await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-lod-distances", "0,16,30");

  const raceLodProfiles = await page.locator("#stage").getAttribute("data-sf3d-race-lod-profiles");
  expect(raceLodProfiles).toContain("s-hunyuan2mv-styled-prototype");
  expect(raceLodProfiles).toContain("s-hunyuan2mv-styled-lod3");
  expect(raceLodProfiles).toContain("s-hunyuan2mv-styled-lod4");

  await page.getByRole("button", { name: "2 Race" }).click();
  await page.waitForTimeout(1800);
  await page.locator("#stage").screenshot({
    path: `${outDir}/hunyuan-styled-race.png`
  });
});


test("animate rigged Hunyuan skeletal proof in Morph Lab and Race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanrigged&modelYaw=90&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(stage).toHaveAttribute("data-sf3d-profile", "s-hunyuan2mv-rigged-proof");
  await expect(stage).toHaveAttribute("data-sf3d-animation", "playing");
  await expect.poll(async () => Number(await stage.getAttribute("data-sf3d-animation-bones"))).toBeGreaterThan(0);

  const sampleBone = async (which) => page.evaluate((target) => {
    const root = target === "lab" ? window.__sf3dAnimatedLab : window.__sf3dAnimatedRace;
    if (!root) return null;
    let bone = null;
    root.traverse((node) => {
      if (!bone && node.isBone && node.name === "fore_L_upper") bone = node;
    });
    if (!bone) return null;
    return [
      Number(bone.quaternion.x.toFixed(6)),
      Number(bone.quaternion.y.toFixed(6)),
      Number(bone.quaternion.z.toFixed(6)),
      Number(bone.quaternion.w.toFixed(6))
    ];
  }, which);

  await page.getByRole("button", { name: "1 Morph" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
  await page.waitForTimeout(250);
  const labA = await sampleBone("lab");
  await page.waitForTimeout(350);
  const labB = await sampleBone("lab");
  expect(labA).not.toBeNull();
  expect(labB).not.toEqual(labA);
  await stage.screenshot({ path: `${outDir}/hunyuan-rigged-lab.png` });

  for (const [label, time] of [["00", 0.00], ["25", 0.25], ["50", 0.50], ["75", 0.75]]) {
    await page.evaluate((t) => {
      window.__sf3dLabMixer?.setTime(t);
    }, time);
    await page.waitForTimeout(60);
    await stage.screenshot({ path: `${outDir}/hunyuan-rigged-side-${label}.png` });
  }

  await page.getByRole("button", { name: "2 Race" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("RACE VIEW");
  await page.waitForTimeout(250);
  const raceA = await sampleBone("race");
  await page.waitForTimeout(350);
  const raceB = await sampleBone("race");
  expect(raceA).not.toBeNull();
  expect(raceB).not.toEqual(raceA);
  await stage.screenshot({ path: `${outDir}/hunyuan-rigged-race.png` });

  console.log("HUNYUAN_RIGGED_BROWSER", JSON.stringify({
    clip: await stage.getAttribute("data-sf3d-animation-clip"),
    bones: Number(await stage.getAttribute("data-sf3d-animation-bones")),
    labA,
    labB,
    raceA,
    raceB
  }));
});


test("compare Hunyuan gait v1 v2 v21 in the same 18-racer race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(210000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  const measureFrames = async () => page.evaluate(() => new Promise((resolve) => {
    const samples = [];
    const started = performance.now();
    let previous = started;
    function tick(now) {
      const elapsed = now - started;
      if (elapsed > 500 && elapsed < 4000) samples.push(now - previous);
      previous = now;
      if (elapsed >= 4200) {
        const sorted = [...samples].sort((a, b) => a - b);
        const avg = samples.reduce((sum, value) => sum + value, 0) / Math.max(1, samples.length);
        const p95 = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))] || 0;
        resolve({
          samples: samples.length,
          averageFrameMs: Number(avg.toFixed(3)),
          averageFps: Number((1000 / avg).toFixed(2)),
          p95FrameMs: Number(p95.toFixed(3))
        });
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }));

  const sampleRig = async (target = "far") => page.evaluate((which) => {
    const model = which === "selected"
      ? window.__hunyuanRacePackRiggedSelected
      : window.__hunyuanRacePackRiggedFar?.[0];
    if (!model) return null;
    const wanted = ["root", "spine", "neck", "fore_L_upper", "fore_R_upper", "hind_L_upper", "hind_R_upper"];
    const values = {};
    model.traverse((node) => {
      if (node.isBone && wanted.includes(node.name)) {
        values[node.name] = [
          Number(node.quaternion.x.toFixed(6)),
          Number(node.quaternion.y.toFixed(6)),
          Number(node.quaternion.z.toFixed(6)),
          Number(node.quaternion.w.toFixed(6))
        ];
      }
      if (node.name === "EvoWild_S_Armature") {
        values.armaturePosition = [
          Number(node.position.x.toFixed(6)),
          Number(node.position.y.toFixed(6)),
          Number(node.position.z.toFixed(6))
        ];
      }
    });
    return values;
  }, target);

  const expectedClips = {
    v1: "EvoWild_S_Run",
    v2: "EvoWild_S_Run_V2",
    v21: "EvoWild_S_Run_V2_1"
  };

  for (const gait of ["v1", "v2", "v21"]) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=${gait}&renderScale=0.75`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );
    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack-gait", gait);
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack-far-animation", expectedClips[gait]);

    await page.getByRole("button", { name: "2 Race" }).click();
    await expect.poll(
      async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
      { timeout: 10000 }
    ).toBe("18,0");

    const a = await sampleRig();
    await page.waitForTimeout(180);
    const b = await sampleRig();
    await page.waitForTimeout(180);
    const c = await sampleRig();
    const perf = await measureFrames();

    expect(a?.fore_L_upper).not.toEqual(b?.fore_L_upper);
    if (gait !== "v1") {
      expect(a?.fore_L_upper).not.toEqual(a?.fore_R_upper);
      expect(a?.hind_L_upper).not.toEqual(a?.hind_R_upper);
      expect(a?.root).not.toEqual(b?.root);
      expect(a?.armaturePosition).not.toEqual(b?.armaturePosition);
    }

    results.push({ gait, clip: expectedClips[gait], a, b, c, perf });
    await stage.screenshot({ path: `${outDir}/hunyuan-gait-${gait}-race.png` });

    if (gait === "v21") {
      await page.getByRole("button", { name: "3 Follow" }).click();
      await expect.poll(
        async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
        { timeout: 10000 }
      ).toBe("17,1");
      for (let phase = 0; phase < 4; phase += 1) {
        await stage.screenshot({ path: `${outDir}/hunyuan-gait-v21-follow-phase${phase + 1}.png` });
        await page.waitForTimeout(210);
      }
      const selectedA = await sampleRig("selected");
      await page.waitForTimeout(210);
      const selectedB = await sampleRig("selected");
      expect(selectedA?.spine).not.toEqual(selectedB?.spine);
    }
  }

  console.log("HUNYUAN_GAIT_TRIPLE_COMPARE", JSON.stringify(
    Object.fromEntries(results.map((result) => [result.gait, result.perf]))
  ));
  fs.writeFileSync(
    `${outDir}/hunyuan-gait-v1-v2-v21-comparison.json`,
    JSON.stringify(results, null, 2)
  );
});


test("compare Hunyuan v21 full-v3 and v3 hybrid race rigs", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(210000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  const measureFrames = async () => page.evaluate(() => new Promise((resolve) => {
    const samples = [];
    const started = performance.now();
    let previous = started;
    function tick(now) {
      const elapsed = now - started;
      if (elapsed > 500 && elapsed < 4000) samples.push(now - previous);
      previous = now;
      if (elapsed >= 4200) {
        const sorted = [...samples].sort((a, b) => a - b);
        const avg = samples.reduce((sum, value) => sum + value, 0) / Math.max(1, samples.length);
        const p95 = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))] || 0;
        resolve({
          samples: samples.length,
          averageFrameMs: Number(avg.toFixed(3)),
          averageFps: Number((1000 / avg).toFixed(2)),
          p95FrameMs: Number(p95.toFixed(3))
        });
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }));

  const inspectRig = async (target = "far") => page.evaluate((which) => {
    const model = which === "selected"
      ? window.__hunyuanRacePackRiggedSelected
      : window.__hunyuanRacePackRiggedFar?.[0];
    if (!model) return null;

    const wanted = [
      "pelvis", "spine", "chest",
      "fore_L_upper", "fore_L_lower", "fore_L_foot",
      "fore_R_upper", "fore_R_lower", "fore_R_foot",
      "hind_L_upper", "hind_L_lower", "hind_L_foot",
      "hind_R_upper", "hind_R_lower", "hind_R_foot"
    ];
    const values = {};
    const bones = [];
    model.traverse((node) => {
      if (node.isBone) {
        bones.push(node.name);
        if (wanted.includes(node.name)) {
          values[node.name] = [
            Number(node.quaternion.x.toFixed(6)),
            Number(node.quaternion.y.toFixed(6)),
            Number(node.quaternion.z.toFixed(6)),
            Number(node.quaternion.w.toFixed(6))
          ];
        }
      }
      if (node.name === "EvoWild_S_Armature_V3" || node.name === "EvoWild_S_Armature") {
        values.armaturePosition = [
          Number(node.position.x.toFixed(6)),
          Number(node.position.y.toFixed(6)),
          Number(node.position.z.toFixed(6))
        ];
      }
    });
    return { boneCount: bones.length, bones, values };
  }, target);

  const expected = {
    v21: { far: "EvoWild_S_Run_V2_1", selected: "EvoWild_S_Run_V2_1" },
    v3: { far: "EvoWild_S_Run_V3", selected: "EvoWild_S_Run_V3" },
    v3hybrid: { far: "EvoWild_S_Run_V2_1", selected: "EvoWild_S_Run_V3" }
  };

  for (const gait of ["v21", "v3", "v3hybrid"]) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=${gait}&renderScale=0.75`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );

    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack-gait", gait);
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack-far-animation", expected[gait].far);
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack-rigged-clip", expected[gait].selected);

    await page.getByRole("button", { name: "2 Race" }).click();
    await expect.poll(
      async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
      { timeout: 10000 }
    ).toBe("18,0");

    const farA = await inspectRig("far");
    await page.waitForTimeout(190);
    const farB = await inspectRig("far");
    const perf = await measureFrames();

    if (gait === "v3") {
      expect(farA?.boneCount).toBe(19);
      expect(farA?.values.fore_L_foot).not.toEqual(farB?.values.fore_L_foot);
    }
    if (gait === "v3hybrid") {
      expect(farA?.boneCount).toBe(13);
    }

    await stage.screenshot({ path: `${outDir}/hunyuan-rig-${gait}-race.png` });

    let selected = null;
    if (gait === "v3hybrid") {
      await page.getByRole("button", { name: "3 Follow" }).click();
      await expect.poll(
        async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
        { timeout: 10000 }
      ).toBe("17,1");

      const selectedA = await inspectRig("selected");
      await page.waitForTimeout(210);
      const selectedB = await inspectRig("selected");
      expect(selectedA?.boneCount).toBe(19);
      for (const name of ["pelvis", "chest", "fore_L_foot", "fore_R_foot", "hind_L_foot", "hind_R_foot"]) {
        expect(selectedA?.bones).toContain(name);
      }
      expect(selectedA?.values.fore_L_foot).not.toEqual(selectedB?.values.fore_L_foot);
      expect(selectedA?.values.pelvis).not.toEqual(selectedB?.values.pelvis);

      for (let phase = 0; phase < 4; phase += 1) {
        await stage.screenshot({ path: `${outDir}/hunyuan-rig-v3hybrid-follow-phase${phase + 1}.png` });
        await page.waitForTimeout(210);
      }
      selected = { a: selectedA, b: selectedB };
    }

    results.push({ gait, farA, farB, selected, perf });
  }

  const byGait = Object.fromEntries(results.map((result) => [result.gait, result]));
  console.log("HUNYUAN_RIG_V3_HYBRID_COMPARE", JSON.stringify({
    v21: byGait.v21.perf,
    v3: byGait.v3.perf,
    v3hybrid: byGait.v3hybrid.perf,
    hybridFarBones: byGait.v3hybrid.farA?.boneCount,
    hybridSelectedBones: byGait.v3hybrid.selected?.a?.boneCount
  }));

  fs.writeFileSync(
    `${outDir}/hunyuan-rig-v21-v3-v3hybrid-comparison.json`,
    JSON.stringify(results, null, 2)
  );
});


test("link Hunyuan stride cadence to live race speed", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=v3hybrid&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
  await expect(stage).toHaveAttribute("data-hunyuan-stride-sync", "speed-linked", { timeout: 10000 });

  const sample = async () => ({
    speed: Number(await stage.getAttribute("data-hunyuan-stride-speed")),
    cruise: Number(await stage.getAttribute("data-hunyuan-stride-cruise")),
    timeScale: Number(await stage.getAttribute("data-hunyuan-stride-time-scale"))
  });

  const early = await sample();
  await page.waitForTimeout(2500);
  const mid = await sample();
  await page.waitForTimeout(2500);
  const later = await sample();

  expect(early.cruise).toBeGreaterThan(0);
  expect(mid.speed).toBeGreaterThan(early.speed);
  expect(mid.timeScale).toBeGreaterThan(early.timeScale);
  expect(later.timeScale).toBeGreaterThanOrEqual(0.28);
  expect(later.timeScale).toBeLessThanOrEqual(1.22);

  await page.getByRole("button", { name: "3 Follow" }).click();
  await expect.poll(
    async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
    { timeout: 10000 }
  ).toBe("17,1");

  const follow = await sample();
  expect(follow.timeScale).toBeGreaterThan(0.28);

  console.log("HUNYUAN_STRIDE_SYNC", JSON.stringify({ early, mid, later, follow }));
});


test("compare Hunyuan v3 and contact-phased v31 hybrid follow rigs", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  const inspect = async () => page.evaluate(() => {
    const model = window.__hunyuanRacePackRiggedSelected;
    if (!model) return null;
    const wanted = ["pelvis", "chest", "fore_L_foot", "fore_R_foot", "hind_L_foot", "hind_R_foot"];
    const values = {};
    model.traverse((node) => {
      if (node.isBone && wanted.includes(node.name)) {
        node.updateWorldMatrix(true, false);
        const e = node.matrixWorld.elements;
        values[node.name] = {
          q: [
            Number(node.quaternion.x.toFixed(6)),
            Number(node.quaternion.y.toFixed(6)),
            Number(node.quaternion.z.toFixed(6)),
            Number(node.quaternion.w.toFixed(6))
          ],
          p: [
            Number(e[12].toFixed(6)),
            Number(e[13].toFixed(6)),
            Number(e[14].toFixed(6))
          ]
        };
      }
    });
    return values;
  });

  for (const gait of ["v3hybrid", "v31hybrid"]) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=${gait}&renderScale=0.75`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );
    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
    await expect(stage).toHaveAttribute("data-hunyuan-stride-sync", "speed-linked", { timeout: 10000 });
    await page.getByRole("button", { name: "3 Follow" }).click();
    await expect.poll(
      async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
      { timeout: 10000 }
    ).toBe("17,1");

    const phases = [];
    for (let i = 0; i < 6; i += 1) {
      phases.push(await inspect());
      await stage.screenshot({ path: `${outDir}/hunyuan-${gait}-contact-phase${i + 1}.png` });
      await page.waitForTimeout(170);
    }

    results.push({
      gait,
      clip: await stage.getAttribute("data-hunyuan-race-pack-rigged-clip"),
      timeScale: Number(await stage.getAttribute("data-hunyuan-stride-time-scale")),
      phases
    });
  }

  expect(results[0].clip).toBe("EvoWild_S_Run_V3");
  expect(results[1].clip).toBe("EvoWild_S_Run_V3_1");
  expect(results[1].timeScale).toBeGreaterThan(0.28);
  expect(results[1].phases[0].fore_L_foot.q).not.toEqual(results[1].phases[3].fore_L_foot.q);
  expect(results[1].phases[0].pelvis.q).not.toEqual(results[1].phases[3].pelvis.q);

  console.log("HUNYUAN_V31_CONTACT_COMPARE", JSON.stringify({
    v3: { clip: results[0].clip, timeScale: results[0].timeScale },
    v31: { clip: results[1].clip, timeScale: results[1].timeScale }
  }));

  fs.writeFileSync(
    `${outDir}/hunyuan-v3-v31-contact-comparison.json`,
    JSON.stringify(results, null, 2)
  );
});


test("validate Hunyuan v4 IK survives GLB export in follow view", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(100000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=v4hybrid&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack-rigged-clip", "EvoWild_S_Run_V4_IK");
  await expect(stage).toHaveAttribute("data-hunyuan-stride-sync", "speed-linked", { timeout: 10000 });

  await page.getByRole("button", { name: "3 Follow" }).click();
  await expect.poll(
    async () => (await stage.getAttribute("data-hunyuan-race-pack-animated-counts")) || "",
    { timeout: 10000 }
  ).toBe("17,1");

  const sample = async () => page.evaluate(() => {
    const model = window.__hunyuanRacePackRiggedSelected;
    if (!model) return null;
    const wanted = [
      "fore_L_upper", "fore_L_lower", "fore_L_foot", "fore_L_target",
      "hind_R_upper", "hind_R_lower", "hind_R_foot", "hind_R_target"
    ];
    const values = {};
    const bones = [];
    model.traverse((node) => {
      if (!node.isBone) return;
      bones.push(node.name);
      if (!wanted.includes(node.name)) return;
      node.updateWorldMatrix(true, false);
      const e = node.matrixWorld.elements;
      values[node.name] = {
        q: [
          Number(node.quaternion.x.toFixed(6)),
          Number(node.quaternion.y.toFixed(6)),
          Number(node.quaternion.z.toFixed(6)),
          Number(node.quaternion.w.toFixed(6))
        ],
        p: [
          Number(e[12].toFixed(6)),
          Number(e[13].toFixed(6)),
          Number(e[14].toFixed(6))
        ]
      };
    });
    return { boneCount: bones.length, bones, values };
  });

  const a = await sample();
  await page.waitForTimeout(220);
  const b = await sample();
  await page.waitForTimeout(220);
  const c = await sample();

  expect(a?.boneCount).toBe(27);
  for (const name of ["fore_L_target", "hind_R_target", "fore_L_upper", "fore_L_lower", "hind_R_upper", "hind_R_lower"]) {
    expect(a?.bones).toContain(name);
  }

  // Targets must animate, and critically the deform IK chain must also change
  // after export. If only the targets move, Blender constraints were not baked.
  expect(a?.values.fore_L_target.p).not.toEqual(c?.values.fore_L_target.p);
  expect(a?.values.fore_L_upper.q).not.toEqual(b?.values.fore_L_upper.q);
  expect(a?.values.fore_L_lower.q).not.toEqual(b?.values.fore_L_lower.q);
  expect(a?.values.hind_R_upper.q).not.toEqual(c?.values.hind_R_upper.q);
  expect(a?.values.hind_R_lower.q).not.toEqual(c?.values.hind_R_lower.q);

  for (let phase = 0; phase < 6; phase += 1) {
    await stage.screenshot({ path: `${outDir}/hunyuan-v4-ik-follow-phase${phase + 1}.png` });
    await page.waitForTimeout(160);
  }

  console.log("HUNYUAN_V4_IK", JSON.stringify({
    boneCount: a?.boneCount,
    clip: await stage.getAttribute("data-hunyuan-race-pack-rigged-clip"),
    timeScale: Number(await stage.getAttribute("data-hunyuan-stride-time-scale")),
    foreTargetA: a?.values.fore_L_target,
    foreTargetC: c?.values.fore_L_target,
    foreUpperA: a?.values.fore_L_upper,
    foreUpperB: b?.values.fore_L_upper
  }));
});


test("inspect Hunyuan v4 IK animation track kinematics", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(80000);

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=v4hybrid&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });

  const info = await page.evaluate(() => {
    const model = window.__hunyuanRacePackRiggedSelected;
    if (!model) return null;

    const animations = [];
    model.traverse((node) => {
      if (node.animations?.length) animations.push(...node.animations);
    });

    const root = model;
    const bones = {};
    model.traverse((node) => {
      if (node.isBone && /fore_L_target|fore_L_foot|fore_L_upper|fore_L_lower/.test(node.name)) {
        bones[node.name] = {
          position: [node.position.x, node.position.y, node.position.z],
          scale: [node.scale.x, node.scale.y, node.scale.z]
        };
      }
    });

    return {
      modelScale: [root.scale.x, root.scale.y, root.scale.z],
      modelPosition: [root.position.x, root.position.y, root.position.z],
      clips: animations.map((clip) => ({
        name: clip.name,
        duration: clip.duration,
        tracks: clip.tracks
          .filter((track) => /fore_L_target|fore_L_foot|fore_L_upper|fore_L_lower/.test(track.name))
          .map((track) => ({
            name: track.name,
            times: Array.from(track.times),
            values: Array.from(track.values)
          }))
      })),
      bones
    };
  });

  console.log("HUNYUAN_V4_TRACKS", JSON.stringify(info));
  expect(info).not.toBeNull();
});


test("calibrate Hunyuan v4 world-space foot slip", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(140000);

  const gains = [0.80, 0.90, 1.00, 1.10, 1.20];
  const results = [];

  const measureSlip = async () => page.evaluate(() => new Promise((resolve) => {
    const samples = [];
    const model = window.__hunyuanRacePackRiggedSelected;
    let foot = null;
    model?.traverse((node) => {
      if (node.isBone && node.name === "fore_L_foot") foot = node;
    });
    if (!foot) {
      resolve({ error: "fore_L_foot_missing" });
      return;
    }

    const started = performance.now();
    let previous = null;

    function tick(now) {
      foot.updateWorldMatrix(true, false);
      const e = foot.matrixWorld.elements;
      const current = {
        t: now,
        x: e[12],
        y: e[13],
        z: e[14]
      };
      if (previous) {
        const dt = Math.max(1e-6, (current.t - previous.t) / 1000);
        const dx = current.x - previous.x;
        const dz = current.z - previous.z;
        samples.push({
          y: (current.y + previous.y) * 0.5,
          horizontalSpeed: Math.hypot(dx, dz) / dt
        });
      }
      previous = current;

      if (now - started >= 1800) {
        const ys = samples.map((s) => s.y).sort((a, b) => a - b);
        const cutoff = ys[Math.min(ys.length - 1, Math.floor(ys.length * 0.32))] ?? Infinity;
        const contact = samples.filter((s) => s.y <= cutoff);
        const avg = (arr) => arr.reduce((sum, value) => sum + value, 0) / Math.max(1, arr.length);
        resolve({
          samples: samples.length,
          contactSamples: contact.length,
          contactYCutoff: Number(cutoff.toFixed(6)),
          contactHorizontalSpeed: Number(avg(contact.map((s) => s.horizontalSpeed)).toFixed(5)),
          allHorizontalSpeed: Number(avg(samples.map((s) => s.horizontalSpeed)).toFixed(5))
        });
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }));

  for (const gain of gains) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=v4hybrid&hunyuanStrideMode=kinematic&hunyuanStrideGain=${gain}&renderScale=0.75`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );

    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
    await page.getByRole("button", { name: "3 Follow" }).click();

    await expect.poll(
      async () => Number(await stage.getAttribute("data-hunyuan-stride-speed")),
      { timeout: 12000, intervals: [250, 250, 500, 500, 750] }
    ).toBeGreaterThan(14.5);

    const before = {
      gain: Number(await stage.getAttribute("data-hunyuan-stride-gain")),
      timeScale: Number(await stage.getAttribute("data-hunyuan-stride-time-scale")),
      raceSpeed: Number(await stage.getAttribute("data-hunyuan-stride-speed")),
      worldSpeed: Number(await stage.getAttribute("data-hunyuan-stride-world-speed")),
      bakedStanceSpeed: Number(await stage.getAttribute("data-hunyuan-stride-baked-stance-speed")),
      curveScale: Number(await stage.getAttribute("data-hunyuan-stride-curve-scale"))
    };
    const slip = await measureSlip();
    results.push({ ...before, ...slip });
  }

  const valid = results.filter((r) => Number.isFinite(r.contactHorizontalSpeed));
  valid.sort((a, b) => a.contactHorizontalSpeed - b.contactHorizontalSpeed);
  expect(valid.length).toBe(gains.length);

  console.log("HUNYUAN_V4_SLIP_CALIBRATION", JSON.stringify({
    best: valid[0],
    ordered: valid
  }));
});


test("compare legacy and calibrated v4 foot slip", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(100000);

  const modes = [
    { name: "legacy", query: "legacy" },
    { name: "kinematic", query: "kinematic" }
  ];
  const results = [];

  const measureSlip = async () => page.evaluate(() => new Promise((resolve) => {
    const model = window.__hunyuanRacePackRiggedSelected;
    let foot = null;
    model?.traverse((node) => {
      if (node.isBone && node.name === "fore_L_foot") foot = node;
    });
    if (!foot) {
      resolve({ error: "fore_L_foot_missing" });
      return;
    }

    const samples = [];
    let previous = null;
    const started = performance.now();

    function tick(now) {
      foot.updateWorldMatrix(true, false);
      const e = foot.matrixWorld.elements;
      const current = { t: now, x: e[12], y: e[13], z: e[14] };

      if (previous) {
        const dt = Math.max(1e-6, (current.t - previous.t) / 1000);
        samples.push({
          y: (current.y + previous.y) * 0.5,
          speed: Math.hypot(current.x - previous.x, current.z - previous.z) / dt
        });
      }
      previous = current;

      if (now - started >= 1900) {
        const ys = samples.map((s) => s.y).sort((a, b) => a - b);
        const cutoff = ys[Math.min(ys.length - 1, Math.floor(ys.length * 0.32))] ?? Infinity;
        const contact = samples.filter((s) => s.y <= cutoff);
        const avg = contact.reduce((sum, s) => sum + s.speed, 0) / Math.max(1, contact.length);
        resolve({
          samples: samples.length,
          contactSamples: contact.length,
          contactHorizontalSpeed: Number(avg.toFixed(5))
        });
        return;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }));

  for (const mode of modes) {
    await page.goto(
      `/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&hunyuanGait=v4hybrid&hunyuanStrideMode=${mode.query}&renderScale=0.75`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );
    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });
    await page.getByRole("button", { name: "3 Follow" }).click();

    await expect.poll(
      async () => Number(await stage.getAttribute("data-hunyuan-stride-speed")),
      { timeout: 12000, intervals: [250, 250, 500, 500, 750] }
    ).toBeGreaterThan(14.5);

    const slip = await measureSlip();
    results.push({
      mode: mode.name,
      sync: await stage.getAttribute("data-hunyuan-stride-sync"),
      gain: Number(await stage.getAttribute("data-hunyuan-stride-gain")),
      timeScale: Number(await stage.getAttribute("data-hunyuan-stride-time-scale")),
      raceSpeed: Number(await stage.getAttribute("data-hunyuan-stride-speed")),
      worldSpeed: Number(await stage.getAttribute("data-hunyuan-stride-world-speed")),
      ...slip
    });
  }

  const legacy = results.find((r) => r.mode === "legacy");
  const kinematic = results.find((r) => r.mode === "kinematic");

  expect(legacy.sync).toBe("speed-linked");
  expect(kinematic.sync).toBe("world-kinematic");
  expect(kinematic.gain).toBeCloseTo(0.9, 3);
  expect(kinematic.contactHorizontalSpeed).toBeLessThan(legacy.contactHorizontalSpeed);

  console.log("HUNYUAN_V4_SLIP_AB", JSON.stringify({
    legacy,
    kinematic,
    reduction: Number(
      ((legacy.contactHorizontalSpeed - kinematic.contactHorizontalSpeed) /
        legacy.contactHorizontalSpeed).toFixed(4)
    )
  }));
});


test("benchmark moving 18 Hunyuan mixed LOD race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });
  const results = [];

  const variants = [
    { name: "double-16-30", side: "double", near: 16, far: 30, renderScale: 0.75 },
    { name: "front-16-30", side: "front", near: 16, far: 30, renderScale: 0.75 },
    { name: "front-14-24", side: "front", near: 14, far: 24, renderScale: 0.75 },
    { name: "front-all-lod4", side: "front", near: 0.1, far: 0.2, renderScale: 0.75 },
    { name: "front-all-lod4-rs05", side: "front", near: 0.1, far: 0.2, renderScale: 0.5 }
  ];

  for (const variant of variants) {
    const params = new URLSearchParams({
      sf3dVariant: "hunyuanstyled",
      sf3dRaceStress: "1",
      sf3dRaceStressMode: "instance",
      sf3dSide: variant.side,
      hunyuanStressNear: String(variant.near),
      hunyuanStressFar: String(variant.far),
      renderScale: String(variant.renderScale)
    });

    await page.goto(
      `/evowild-test/?${params.toString()}`,
      { waitUntil: "domcontentloaded", timeout: 30000 }
    );
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d-race-stress", "ready", { timeout: 50000 });

    const metrics = await page.evaluate(() => window.__sf3dRaceStress);
    expect(metrics?.racers).toBe(18);
    expect(metrics?.mode).toBe("instance");
    expect(metrics?.label).toBe("hunyuan");
    expect(metrics?.distances).toEqual([variant.near, variant.far]);
    expect(metrics?.levelTriangles?.length).toBe(3);
    expect(metrics?.averageModelTriangles).toBeLessThanOrEqual(metrics?.allBaseTriangles);
    expect(metrics?.maxLevelCounts?.slice(1).some((count) => count > 0)).toBe(true);

    results.push({ name: variant.name, ...metrics });
    console.log("HUNYUAN_MIXED_LOD_VARIANT", JSON.stringify({ name: variant.name, ...metrics }));
    await page.locator("#stage").screenshot({
      path: `${outDir}/hunyuan-mixed-${variant.name}.png`
    });
  }

  const baseline = results.find((result) => result.name === "double-16-30");
  const allLod4 = results.find((result) => result.name === "front-all-lod4");
  expect(allLod4.averageModelTriangles).toBeLessThan(baseline.averageModelTriangles);

  fs.writeFileSync(
    `${outDir}/hunyuan-mixed-lod-race-variants.json`,
    JSON.stringify(results, null, 2)
  );
});


test("capture Hunyuan LOD4 final views", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  for (const yaw of [180, 270]) {
    const params = new URLSearchParams({
      sf3dVariant: "hunyuanlod4",
      modelYaw: String(yaw)
    });
    await page.goto(`/evowild-test/?${params.toString()}`, { waitUntil: "networkidle" });
    await expect(page.locator("#stage")).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
    await expect(page.locator("#stage")).toHaveAttribute("data-model-yaw", String(yaw), { timeout: 20000 });
    await page.getByRole("button", { name: "1 Morph" }).click();
    await expect(page.locator("#viewLabel")).toHaveText("MORPH LAB");
    await page.waitForTimeout(250);
    await page.locator("#stage").screenshot({
      path: `${outDir}/hunyuan4-lod4-yaw${yaw}.png`
    });
  }
});

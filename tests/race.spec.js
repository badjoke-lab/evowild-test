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


test("run S-only Hunyuan 18-racer pack with race and follow LOD policy", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(70000);

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto(
    "/evowild-test/?sf3dVariant=hunyuanstyled&hunyuanRacePack=1&hunyuanRacePackSide=front&renderScale=0.75",
    { waitUntil: "domcontentloaded", timeout: 30000 }
  );

  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-sf3d", "loaded", { timeout: 20000 });
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack", "loaded", { timeout: 30000 });

  await page.getByRole("button", { name: "2 Race" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("RACE VIEW");
  await expect.poll(
    async () => (await stage.getAttribute("data-hunyuan-race-pack-counts")) || "",
    { timeout: 10000 }
  ).toMatch(/^0,\d+,\d+$/);

  const raceCounts = (await stage.getAttribute("data-hunyuan-race-pack-counts"))
    .split(",")
    .map(Number);
  expect(raceCounts.reduce((sum, value) => sum + value, 0)).toBe(18);
  expect(raceCounts[2]).toBeGreaterThan(raceCounts[1]);
  await stage.screenshot({ path: `${outDir}/hunyuan-s-only-race-pack.png` });

  await page.getByRole("button", { name: "3 Follow" }).click();
  await expect(page.locator("#viewLabel")).toHaveText("FOLLOW VIEW");
  await expect.poll(
    async () => (await stage.getAttribute("data-hunyuan-race-pack-counts")) || "",
    { timeout: 10000 }
  ).toMatch(/^1,\d+,\d+$/);

  const followCounts = (await stage.getAttribute("data-hunyuan-race-pack-counts"))
    .split(",")
    .map(Number);
  expect(followCounts.reduce((sum, value) => sum + value, 0)).toBe(17);
  expect(followCounts[0]).toBe(0);
  expect(followCounts[2]).toBeGreaterThan(0);
  expect(followCounts[1]).toBeLessThan(17);
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack-rigged-selected", "visible");
  await expect(stage).toHaveAttribute("data-hunyuan-race-pack-rigged", "playing");

  const sampleSelectedRigBone = async () => page.evaluate(() => {
    const root = window.__hunyuanRacePackRiggedSelected;
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
  });
  const rigA = await sampleSelectedRigBone();
  await page.waitForTimeout(350);
  const rigB = await sampleSelectedRigBone();
  expect(rigA).not.toBeNull();
  expect(rigB).not.toEqual(rigA);

  await stage.screenshot({ path: `${outDir}/hunyuan-s-only-follow-pack.png` });

  console.log("HUNYUAN_S_ONLY_PACK", JSON.stringify({
    raceCounts,
    followCounts,
    rigA,
    rigB,
    side: await stage.getAttribute("data-hunyuan-race-pack-side"),
    profiles: await stage.getAttribute("data-hunyuan-race-pack-profiles"),
    triangles: await stage.getAttribute("data-hunyuan-race-pack-triangles")
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

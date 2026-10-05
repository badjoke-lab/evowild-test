import { test, expect } from "@playwright/test";
import fs from "node:fs";

const REVIEW_ASSET = "public/experiments/tripo-s/t1-steady-run.glb";
const hasRealT1Asset = fs.existsSync(REVIEW_ASSET);

function captureErrors(page) {
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  return { pageErrors, consoleErrors };
}

test("Tripo T1 steady-run exports four review views", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.skip(!hasRealT1Asset, "Waiting for committed real Tripo T1 GLB");
  test.setTimeout(45000);

  const { pageErrors, consoleErrors } = captureErrors(page);
  const outDir = "artifacts/tripo-motion-review";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/tripo-motion-review.html", { waitUntil: "networkidle" });
  await expect(page.locator("body")).toHaveAttribute("data-review-state", "ready", { timeout: 20000 });

  const clipCount = Number(await page.locator("body").getAttribute("data-clip-count"));
  const boneCount = Number(await page.locator("body").getAttribute("data-bone-count"));
  const duration = Number(await page.locator("body").getAttribute("data-clip-duration"));

  expect(clipCount).toBeGreaterThan(0);
  expect(boneCount).toBeGreaterThan(0);
  expect(duration).toBeGreaterThan(0.5);

  const views = ["SIDE", "LOW", "CHASE", "FRONT"];
  for (const view of views) {
    await page.getByRole("button", { name: view, exact: true }).click();
    await expect(page.locator("#cameraReadout")).toHaveText(view);
    await page.waitForTimeout(900);
    await page.screenshot({
      path: `${outDir}/tripo-t1-${view.toLowerCase()}.png`,
      fullPage: true
    });
  }

  fs.writeFileSync(
    `${outDir}/runtime-metadata.json`,
    JSON.stringify({ clipCount, boneCount, duration }, null, 2) + "\n"
  );

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

test("Tripo T1 steady-run records continuous motion review", async ({ browser }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.skip(!hasRealT1Asset, "Waiting for committed real Tripo T1 GLB");
  test.setTimeout(45000);

  const outDir = "artifacts/tripo-motion-review";
  fs.mkdirSync(outDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outDir,
      size: { width: 1280, height: 720 }
    }
  });
  const page = await context.newPage();
  const { pageErrors, consoleErrors } = captureErrors(page);

  await page.goto("http://127.0.0.1:4173/evowild-test/tripo-motion-review.html", {
    waitUntil: "networkidle"
  });
  await expect(page.locator("body")).toHaveAttribute("data-review-state", "ready", { timeout: 20000 });

  for (const view of ["SIDE", "LOW", "CHASE", "FRONT"]) {
    await page.getByRole("button", { name: view, exact: true }).click();
    await page.waitForTimeout(1800);
  }

  const video = page.video();
  await page.close();
  if (!video) throw new Error("Tripo T1 review video was not created");
  await video.saveAs(`${outDir}/tripo-t1-motion-review.webm`);
  await context.close();

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

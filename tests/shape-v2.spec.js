import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S shape-v2 baseline comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(90000);

  const outDir = "test-results/shape-v2";
  fs.mkdirSync(outDir, { recursive: true });

  const errors = [];
  page.on("pageerror", (err) => errors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  async function capture(url, expectedAsset, prefix) {
    await page.goto(url, { waitUntil: "networkidle" });
    const scene = page.locator("#scene");
    await expect(scene).toBeVisible();
    await expect(scene).toHaveAttribute("data-s-asset-ready", "1", { timeout: 30000 });
    await expect(scene).toHaveAttribute("data-s-asset", expectedAsset);

    const result = {};
    for (const view of ["SIDE", "LOW", "CHASE", "FRONT"]) {
      await page.getByRole("button", { name: view, exact: true }).click({ force: true });
      await expect(page.locator("#cameraReadout")).toHaveText(view);
      await page.waitForTimeout(450);
      const path = `${outDir}/${prefix}-${view.toLowerCase()}.png`;
      const buffer = await scene.screenshot({ path });
      result[view] = crypto.createHash("sha256").update(buffer).digest("hex");
    }
    return result;
  }

  const baseline = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S",
    "hunyuan-s-lod2",
    "baseline"
  );
  const candidate = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v2",
    "hunyuan-s-lod2-shape-v2",
    "shape-v2"
  );

  expect(candidate.SIDE).not.toBe(baseline.SIDE);
  expect(candidate.FRONT).not.toBe(baseline.FRONT);
  expect(errors, errors.join("\n")).toEqual([]);

  console.log("SHAPE_V2_BROWSER", JSON.stringify({ baseline, candidate }));
});

import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S v15 v16 comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);
  const outDir = "test-results/shape-v16-browser";
  fs.mkdirSync(outDir, { recursive: true });
  const errors = [];
  page.on("pageerror", (err) => errors.push(err.stack || String(err)));
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });

  async function capture(shape, expectedAsset, prefix) {
    await page.goto(
      `/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=${shape}`,
      { waitUntil: "networkidle" }
    );
    const scene = page.locator("#scene");
    await expect(scene).toBeVisible();
    await expect(scene).toHaveAttribute("data-s-asset-ready", "1", { timeout: 30000 });
    await expect(scene).toHaveAttribute("data-s-asset", expectedAsset);
    const result = {};
    for (const view of ["LOW", "FRONT", "CHASE", "SIDE"]) {
      await page.getByRole("button", { name: view, exact: true }).click({ force: true });
      await expect(page.locator("#cameraReadout")).toHaveText(view);
      await page.waitForTimeout(220);
      const path = `${outDir}/${prefix}-${view.toLowerCase()}.png`;
      const buffer = await scene.screenshot({ path });
      result[view] = crypto.createHash("sha256").update(buffer).digest("hex");
    }
    return result;
  }

  const v15 = await capture("v15", "hunyuan-s-lod2-shape-v15", "shape-v15");
  const v16 = await capture("v16", "hunyuan-s-lod2-shape-v16", "shape-v16");

  expect(v16.LOW).not.toBe(v15.LOW);
  expect(v16.FRONT).not.toBe(v15.FRONT);
  expect(v16.CHASE).not.toBe(v15.CHASE);
  expect(v16.SIDE).not.toBe(v15.SIDE);
  expect(errors, errors.join("\n")).toEqual([]);
  console.log("SHAPE_V16_BROWSER", JSON.stringify({ v15, v16 }));
});

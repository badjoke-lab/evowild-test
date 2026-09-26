import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S shape baseline v3 v4 comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const outDir = "test-results/shape-v4-browser";
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
      await page.waitForTimeout(260);
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
  const v3 = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v3",
    "hunyuan-s-lod2-shape-v3",
    "shape-v3"
  );
  const v4 = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v4",
    "hunyuan-s-lod2-shape-v4",
    "shape-v4"
  );

  expect(v4.SIDE).not.toBe(v3.SIDE);
  expect(v4.LOW).not.toBe(v3.LOW);
  expect(v4.FRONT).not.toBe(v3.FRONT);
  expect(errors, errors.join("\n")).toEqual([]);

  console.log("SHAPE_V4_BROWSER", JSON.stringify({ baseline, v3, v4 }));
});

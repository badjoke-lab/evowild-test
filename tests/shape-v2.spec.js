import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S shape baseline v4 v5 comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(150000);

  const outDir = "test-results/shape-v5-browser";
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
  const v4 = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v4",
    "hunyuan-s-lod2-shape-v4",
    "shape-v4"
  );
  const v5 = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v5",
    "hunyuan-s-lod2-shape-v5",
    "shape-v5"
  );

  expect(v5.SIDE).not.toBe(v4.SIDE);
  expect(v5.LOW).not.toBe(v4.LOW);
  expect(v5.FRONT).not.toBe(v4.FRONT);
  expect(errors, errors.join("\n")).toEqual([]);

  console.log("SHAPE_V5_BROWSER", JSON.stringify({ baseline, v4, v5 }));
});

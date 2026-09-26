import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S shape v4 v5 v51 comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(160000);

  const outDir = "test-results/shape-v51-browser";
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
  const v51 = await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v51",
    "hunyuan-s-lod2-shape-v51",
    "shape-v51"
  );

  expect(v51.SIDE).not.toBe(v5.SIDE);
  expect(v51.LOW).not.toBe(v5.LOW);
  expect(v51.FRONT).not.toBe(v5.FRONT);
  expect(errors, errors.join("\n")).toEqual([]);

  console.log("SHAPE_V51_BROWSER", JSON.stringify({ v4, v5, v51 }));
});

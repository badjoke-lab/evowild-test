import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Sakura NPR lane keeps named cameras on the correct S forward axis and captures visuals", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(45000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.stack || String(err)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const outDir = "test-results/visuals";
  fs.mkdirSync(outDir, { recursive: true });

  await page.goto("/evowild-test/preview-sakura-npr/index.html", { waitUntil: "networkidle" });
  const canvas = page.locator("#view");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-render-lane", "sakura-npr");
  await expect(canvas).toHaveAttribute("data-camera-axis-fix", "1");
  await expect(canvas).toHaveAttribute("data-head-silhouette-correction", "1");
  await expect(canvas).toHaveAttribute("data-native-forward-axis", "-Z");
  await expect(canvas).toHaveAttribute("data-runtime-forward-axis", "+Z");

  await page.waitForTimeout(900);

  async function cameraDot() {
    return page.evaluate(() => {
      const { model, camera, THREE } = window.__nprLane;
      const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(model.quaternion);
      forward.y = 0;
      forward.normalize();

      const box = new THREE.Box3().setFromObject(model);
      const size = new THREE.Vector3();
      box.getSize(size);
      const target = new THREE.Vector3(0, Math.max(1, size.y) * 0.48, 0);
      const view = camera.position.clone().sub(target).normalize();

      return {
        dot: view.dot(forward),
        x: camera.position.x,
        y: camera.position.y,
        z: camera.position.z
      };
    });
  }

  await page.getByRole("button", { name: "FRONT", exact: true }).click();
  await page.waitForTimeout(200);
  const front = await cameraDot();
  expect(front.dot).toBeGreaterThan(0.72);
  await canvas.screenshot({ path: `${outDir}/sakura-npr-front.png` });

  await page.getByRole("button", { name: "CHASE", exact: true }).click();
  await page.waitForTimeout(200);
  const chase = await cameraDot();
  expect(chase.dot).toBeLessThan(-0.72);
  await canvas.screenshot({ path: `${outDir}/sakura-npr-chase.png` });

  await page.getByRole("button", { name: "SIDE", exact: true }).click();
  await page.waitForTimeout(200);
  const side = await cameraDot();
  expect(Math.abs(side.dot)).toBeLessThan(0.2);
  await canvas.screenshot({ path: `${outDir}/sakura-npr-side.png` });

  await page.getByRole("button", { name: "3/4", exact: true }).click();
  await page.waitForTimeout(200);
  await canvas.screenshot({ path: `${outDir}/sakura-npr-threeq.png` });

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);
});

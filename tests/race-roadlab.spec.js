import { test, expect } from "@playwright/test";
import fs from "node:fs";

async function assertRunning(page, shot) {
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(String(err)));

  await page.goto(`/evowild-test/race-roadlab.html?shot=${shot}`, { waitUntil: "networkidle" });
  const stage = page.locator(".roadlab");

  await expect(stage).toHaveAttribute("data-state", "ready", { timeout: 10000 });
  await expect(stage).toHaveAttribute("data-running", "true", { timeout: 5000 });
  await expect(stage).toHaveAttribute("data-loaded-morphs", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-direction-set", "five-directions-all-morphs");
  await expect(stage).toHaveAttribute("data-loaded-direction-target", "side,front_3q,front,back_3q,back");
  await expect(stage).toHaveAttribute("data-camera-mode", shot === "front3q" ? "front_3q" : shot === "back3q" ? "back_3q" : shot);

  const expectedDirection = shot === "front3q" ? "front_3q" : shot === "back3q" ? "back_3q" : shot;
  await expect(stage).toHaveAttribute("data-selected-direction", expectedDirection, { timeout: 5000 });

  const frames = new Set();
  for (let i = 0; i < 5; i++) {
    frames.add(await stage.getAttribute("data-frame"));
    await page.waitForTimeout(110);
  }
  expect(frames.size).toBeGreaterThanOrEqual(2);
  expect(pageErrors).toEqual([]);
  return stage;
}

test("Road Lab renders animated S/P/E/A morph race", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Road Lab visual proof runs on desktop only");
  test.setTimeout(90000);

  fs.mkdirSync("test-results/visuals", { recursive: true });

  for (const shot of ["side","front3q","back3q"]) {
    const stage = await assertRunning(page, shot);
    await page.waitForTimeout(900);
    await page.screenshot({
      path: `test-results/visuals/desktop-roadlab-${shot}.png`,
      fullPage: false,
      animations: "disabled"
    });
  }
});


test("Road Lab directional atlases have six distinct frames per row", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "asset diagnostics run on desktop only");
  test.setTimeout(45000);

  const atlases = [
    ["P", "/evowild-test/concept/p-multidirection-run-atlas.svg"],
    ["E", "/evowild-test/concept/e-multidirection-run-atlas.svg"],
    ["A", "/evowild-test/concept/a-multidirection-run-atlas.svg"]
  ];

  fs.mkdirSync("test-results/visuals", { recursive: true });

  for (const [morph, src] of atlases) {
    await page.goto("/evowild-test/race-roadlab.html", { waitUntil: "networkidle" });

    const metrics = await page.evaluate(async ({ src }) => {
      const img = new Image();
      img.src = src;
      await img.decode();

      const cols = 6;
      const rows = 4;
      const cellW = img.naturalWidth / cols;
      const cellH = img.naturalHeight / rows;

      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      ctx.drawImage(img, 0, 0);

      const rowMetrics = [];
      for (let row = 0; row < rows; row++) {
        const frames = [];
        for (let col = 0; col < cols; col++) {
          frames.push(ctx.getImageData(col * cellW, row * cellH, cellW, cellH).data);
        }

        const pairDiffs = [];
        for (let i = 0; i < cols; i++) {
          const a = frames[i];
          const b = frames[(i + 1) % cols];
          let diff = 0;
          let visible = 0;
          for (let p = 0; p < a.length; p += 4) {
            if (a[p + 3] > 10 || b[p + 3] > 10) {
              diff += Math.abs(a[p] - b[p]) + Math.abs(a[p + 1] - b[p + 1]) + Math.abs(a[p + 2] - b[p + 2]);
              visible++;
            }
          }
          pairDiffs.push(visible ? diff / visible / 3 : 0);
        }
        rowMetrics.push(pairDiffs);
      }

      document.body.innerHTML = "";
      document.body.style.margin = "0";
      document.body.style.background = "#1a2028";
      const preview = document.createElement("img");
      preview.src = src;
      preview.style.width = "864px";
      preview.style.height = "768px";
      preview.style.imageRendering = "pixelated";
      document.body.appendChild(preview);

      return { naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight, rowMetrics };
    }, { src });

    console.log("ROADLAB_ATLAS_METRICS", morph, JSON.stringify(metrics));

    expect(metrics.naturalWidth).toBeGreaterThanOrEqual(864);
    expect(metrics.naturalHeight).toBeGreaterThanOrEqual(768);

    for (const row of metrics.rowMetrics) {
      expect(row.filter(v => v > 3).length).toBeGreaterThanOrEqual(4);
    }

    await page.screenshot({
      path: `test-results/visuals/desktop-${morph.toLowerCase()}-direction-atlas.png`,
      fullPage: true
    });
  }
});

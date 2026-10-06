import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

test("capture P E A canonical gait keyposes with transparent background", async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 768, height: 512 });
  const rawDir = process.env.PEA_KEYPOSE_RAW_DIR || "/tmp/pea-keypose-capture/raw";
  fs.mkdirSync(rawDir, { recursive: true });

  for (const morph of ["P", "E", "A"]) {
    for (let phase = 0; phase < 12; phase += 1) {
      await page.goto(
        `/evowild-test/preview-motion-first/index.html?motion=1&morph=${morph}&spriteCapture=1&spritePhase=${phase}`,
        { waitUntil: "networkidle" }
      );
      const canvas = page.locator("#scene");
      await expect(canvas).toHaveAttribute("data-sprite-capture-ready", "1", { timeout: 15000 });
      await expect(canvas).toHaveAttribute("data-sprite-capture-morph", morph);
      await expect(canvas).toHaveAttribute("data-sprite-capture-phase", String(phase));
      await expect(canvas).toHaveAttribute("data-sprite-capture-alpha", "0");
      await expect(canvas).toHaveAttribute("data-sprite-capture-chroma", "#00ff00");
      await expect(canvas).toHaveAttribute("data-sprite-capture-world", "hidden");
      await expect(canvas).toHaveAttribute("data-sprite-capture-camera", "SIDE_LOCKED");
      await page.waitForTimeout(180);
      const dataUrl = await canvas.evaluate((node) => node.toDataURL("image/png"));
      const payload = dataUrl.replace(/^data:image\/png;base64,/, "");
      const outputPath = path.join(rawDir, `${morph.toLowerCase()}-${phase}.png`);
      const buffer = Buffer.from(payload, "base64");
      expect(buffer.length).toBeGreaterThan(1000);
      fs.writeFileSync(outputPath, buffer);
      expect(fs.existsSync(outputPath)).toBe(true);
    }
  }
  const captures = fs.readdirSync(rawDir).filter((name) => name.endsWith(".png"));
  expect(captures).toHaveLength(36);
});

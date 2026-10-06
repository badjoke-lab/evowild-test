import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("capture P E A canonical gait keyposes with transparent background", async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 768, height: 512 });
  fs.mkdirSync("artifacts/pea-keypose-capture/raw", { recursive: true });

  for (const morph of ["P", "E", "A"]) {
    for (let phase = 0; phase < 6; phase += 1) {
      await page.goto(
        `/evowild-test/preview-motion-first/index.html?motion=1&morph=${morph}&spriteCapture=1&spritePhase=${phase}`,
        { waitUntil: "networkidle" }
      );
      const canvas = page.locator("#scene");
      await expect(canvas).toHaveAttribute("data-sprite-capture-ready", "1", { timeout: 15000 });
      await expect(canvas).toHaveAttribute("data-sprite-capture-morph", morph);
      await expect(canvas).toHaveAttribute("data-sprite-capture-phase", String(phase));
      await expect(canvas).toHaveAttribute("data-sprite-capture-alpha", "1");
      await expect(canvas).toHaveAttribute("data-sprite-capture-world", "hidden");
      await expect(canvas).toHaveAttribute("data-sprite-capture-camera", "SIDE_LOCKED");
      await page.waitForTimeout(180);
      const dataUrl = await canvas.evaluate((node) => node.toDataURL("image/png"));
      const payload = dataUrl.replace(/^data:image\/png;base64,/, "");
      fs.writeFileSync(
        `artifacts/pea-keypose-capture/raw/${morph.toLowerCase()}-${phase}.png`,
        Buffer.from(payload, "base64")
      );
    }
  }
});

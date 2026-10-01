import { test, expect } from "@playwright/test";
import fs from "node:fs";
import crypto from "node:crypto";

test("render S baseline v27 conservative comparison", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  test.setTimeout(120000);
  const outDir = "test-results/shape-v27-browser";
  fs.mkdirSync(outDir, { recursive: true });

  const errors=[];
  page.on("pageerror",(err)=>errors.push(err.stack||String(err)));
  page.on("console",(msg)=>{ if(msg.type()==="error") errors.push(msg.text()); });

  async function capture(url, expectedAsset, prefix) {
    await page.goto(url,{waitUntil:"networkidle"});
    const scene=page.locator("#scene");
    await expect(scene).toBeVisible();
    await expect(scene).toHaveAttribute("data-s-asset-ready","1",{timeout:30000});
    await expect(scene).toHaveAttribute("data-s-asset",expectedAsset);
    const result={};
    for(const view of ["LOW","FRONT","CHASE","SIDE"]) {
      await page.getByRole("button",{name:view,exact:true}).click({force:true});
      await expect(page.locator("#cameraReadout")).toHaveText(view);
      await page.waitForTimeout(220);
      const path=`${outDir}/${prefix}-${view.toLowerCase()}.png`;
      const buffer=await scene.screenshot({path});
      result[view]=crypto.createHash("sha256").update(buffer).digest("hex");
    }
    return result;
  }

  const baseline=await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S",
    "hunyuan-s-lod2",
    "baseline"
  );
  const v27=await capture(
    "/evowild-test/preview-motion-first/index.html?inspect=1&morph=S&shape=v27",
    "hunyuan-s-lod2-shape-v27",
    "shape-v27"
  );

  expect(v27.LOW).not.toBe(baseline.LOW);
  expect(v27.FRONT).not.toBe(baseline.FRONT);
  expect(v27.CHASE).not.toBe(baseline.CHASE);
  expect(errors, errors.join("\n")).toEqual([]);
  console.log("SHAPE_V27_BROWSER", JSON.stringify({baseline,v27}));
});

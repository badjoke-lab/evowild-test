import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S-only hybrid renders animated sprites on a Three.js course", async ({ page }, testInfo) => {
  const pageErrors=[];
  const consoleErrors=[];
  page.on("pageerror",e=>pageErrors.push(e.stack||String(e)));
  page.on("console",m=>{if(m.type()==="error")consoleErrors.push(m.text());});

  await page.goto("/evowild-test/race-s-hybrid.html",{waitUntil:"networkidle"});
  const stage=page.locator("#stage");

  await expect(stage).toHaveAttribute("data-mode","s-only-hybrid");
  await expect(stage).toHaveAttribute("data-renderer","three-sprite-hybrid");
  await expect(stage).toHaveAttribute("data-webgl-ready","true");
  await expect(stage).toHaveAttribute("data-s-run-sheet","ready",{timeout:10000});
  await expect(stage).toHaveAttribute("data-race-state","running",{timeout:12000});

  await page.waitForTimeout(2300);

  const distance=Number(await stage.getAttribute("data-selected-distance"));
  const speed=Number(await stage.getAttribute("data-selected-speed"));
  const frame=Number(await stage.getAttribute("data-s-run-frame"));
  const phase=await stage.getAttribute("data-s-run-phase");
  const cameraDistance=Number(await stage.getAttribute("data-camera-distance"));

  expect(distance).toBeGreaterThan(0);
  expect(speed).toBeGreaterThan(14);
  expect(frame).toBeGreaterThanOrEqual(0);
  expect(frame).toBeLessThan(6);
  expect(["CONTACT","PUSH","LIFT","FLIGHT","REACH","LAND"]).toContain(phase);
  expect(cameraDistance).toBeGreaterThan(8);
  expect(cameraDistance).toBeLessThan(22);
  expect(await stage.getAttribute("data-hybrid-camera")).toBe("side-chase");
  expect(pageErrors,pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors,consoleErrors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals",{recursive:true});
  await stage.screenshot({
    path:`test-results/visuals/${testInfo.project.name}-s-hybrid.png`
  });

  await expect.poll(
    async()=>Number(await stage.getAttribute("data-selected-distance")),
    {timeout:12000,intervals:[250,500,750]}
  ).toBeGreaterThan(190);

  expect(Number(await stage.getAttribute("data-selected-rank"))).toBeLessThan(8);
  expect(pageErrors,pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors,consoleErrors.join("\n")).toEqual([]);

  await stage.screenshot({
    path:`test-results/visuals/${testInfo.project.name}-s-hybrid-race.png`
  });
});
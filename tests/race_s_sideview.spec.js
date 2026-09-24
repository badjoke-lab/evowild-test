import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S-only sideview rebuild aligns motion and race direction", async ({ page }, testInfo) => {
  const pageErrors=[];
  const consoleErrors=[];
  page.on("pageerror", e=>pageErrors.push(e.stack||String(e)));
  page.on("console", m=>{ if(m.type()==="error") consoleErrors.push(m.text()); });

  await page.goto("/evowild-test/race-s-sideview.html", { waitUntil:"networkidle" });

  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-mode","s-only-sideview");
  await expect(stage).toHaveAttribute("data-renderer","side-perspective");
  await expect(stage).toHaveAttribute("data-s-run-sheet","ready",{timeout:10000});
  await expect(stage).toHaveAttribute("data-race-state","running",{timeout:8000});

  await page.waitForTimeout(1500);

  const distance=Number(await stage.getAttribute("data-selected-distance"));
  const speed=Number(await stage.getAttribute("data-selected-speed"));
  const frame=Number(await stage.getAttribute("data-s-run-frame"));
  const phase=await stage.getAttribute("data-s-run-phase");
  const x=Number(await stage.getAttribute("data-selected-x"));
  const visible=Number(await stage.getAttribute("data-visible-racers"));
  const fieldMinX=Number(await stage.getAttribute("data-field-min-x"));
  const fieldMaxX=Number(await stage.getAttribute("data-field-max-x"));

  expect(distance).toBeGreaterThan(0);
  expect(speed).toBeGreaterThan(0);
  expect(frame).toBeGreaterThanOrEqual(0);
  expect(frame).toBeLessThan(6);
  expect(["CONTACT","PUSH","LIFT","FLIGHT","REACH","LAND"]).toContain(phase);
  const viewportWidth=await page.evaluate(()=>innerWidth);
  expect(visible).toBe(8);
  expect(fieldMinX).toBeGreaterThanOrEqual(0);
  expect(fieldMaxX).toBeLessThanOrEqual(viewportWidth);
  expect(speed).toBeGreaterThan(14);
  expect(pageErrors,pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors,consoleErrors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals",{recursive:true});
  await stage.screenshot({path:`test-results/visuals/${testInfo.project.name}-s-sideview.png`});

  await expect.poll(
    async()=>Number(await stage.getAttribute("data-selected-distance")),
    { timeout:12000, intervals:[250,500,750] }
  ).toBeGreaterThan(190);

  const bank=Number(await stage.getAttribute("data-course-bank"));
  expect(Math.abs(bank)).toBeGreaterThan(2);
  expect(Number(await stage.getAttribute("data-visible-racers"))).toBe(8);
  expect(pageErrors,pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors,consoleErrors.join("\n")).toEqual([]);

  await stage.screenshot({
    path:`test-results/visuals/${testInfo.project.name}-s-sideview-bank.png`
  });
});
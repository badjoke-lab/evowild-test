import {test,expect} from "@playwright/test";
import {
  OVAL_DISTANCE, OVAL_RADIUS, wrapOvalDistance, ovalWorld, ovalChaseCamera,
  projectOvalRunner, ovalSegmentAt,ovalMinimapPoint
} from "../src/oval_course_2p5d.js";

test("continuous closed 1600m oval connects both straights and turns",()=>{
  expect(OVAL_DISTANCE).toBe(1600);
  const start=ovalWorld(0), finish=ovalWorld(1600);
  expect(Math.hypot(start.x-finish.x,start.z-finish.z)).toBeLessThan(1e-8);
  expect(Math.hypot(start.tx-finish.tx,start.tz-finish.tz)).toBeLessThan(1e-8);
  for(const boundary of [500,800,1300,1600]){
    const a=ovalWorld(boundary-.001),b=ovalWorld(boundary+.001);
    expect(Math.hypot(a.x-b.x,a.z-b.z)).toBeLessThan(.003);
    expect(Math.hypot(a.tx-b.tx,a.tz-b.tz)).toBeLessThan(.0001);
  }
  expect(ovalSegmentAt(100)).toBe("HOME_STRAIGHT");
  expect(ovalSegmentAt(650)).toBe("FIRST_TURN");
  expect(ovalSegmentAt(1000)).toBe("BACK_STRAIGHT");
  expect(ovalSegmentAt(1500)).toBe("FINAL_TURN");
  expect(wrapOvalDistance(-1)).toBe(1599);
  expect(OVAL_RADIUS).toBeGreaterThan(95);
});
test("inside/outside lanes stay apart and camera looks along heading throughout oval",()=>{
  for(const m of [20,490,550,780,820,1260,1340,1595]){
    const a=ovalWorld(m,0),b=ovalWorld(m,3);
    const separation=Math.hypot(a.x-b.x,a.z-b.z);
    expect(separation).toBeCloseTo(9.6,3);
    const cam=ovalChaseCamera(m,1.5);
    const me=projectOvalRunner(cam,m,1.5,1280,720);
    const ahead=projectOvalRunner(cam,m+18,1.5,1280,720);
    expect(me).not.toBeNull();
    expect(ahead).not.toBeNull();
    expect(me.depth).toBeGreaterThan(35);
    expect(ahead.depth).toBeGreaterThan(me.depth);
    expect(ahead.y).toBeLessThan(me.y);
    const pin=ovalMinimapPoint(m,5,5,320,140);
    expect(Number.isFinite(pin.x)&&Number.isFinite(pin.y)).toBe(true);
  }
});
test("3/4 oval is the default spectator camera; can switch to legacy side",async ({page})=>{
  await page.goto("/evowild-test/race-stadium.html?autoStart=1",{waitUntil:"networkidle"});
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-camera-mode","oval-three-quarter-follow");
  await expect(stage).toHaveAttribute("data-track-geometry","world-space-1600m-oval");
  await expect(stage).toHaveAttribute("data-track-segment","HOME_STRAIGHT");
  await expect(stage).toHaveAttribute("data-track-visible","1");
  await expect(stage).toHaveAttribute("data-creature-facing","side-billboard-provisional");
  await expect(stage).toHaveAttribute("data-orb-count",/[1-9]\d*/);
  await page.locator("#cameraMode").click();
  await expect(stage).toHaveAttribute("data-camera-mode","legacy-side");
  await expect(stage).toHaveAttribute("data-track-visible","0");
  await page.locator("#cameraMode").click();
  await expect(stage).toHaveAttribute("data-camera-mode","oval-three-quarter-follow");
});
test("real 3/4 follow screenshot is archived in CI for both desktop and mobile",async ({page},testInfo)=>{
  await page.goto("/evowild-test/race-stadium.html?autoStart=1",{waitUntil:"networkidle"});
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-race-state","running",{timeout:9500});
  await expect(stage).toHaveAttribute("data-agent-decision-count",/[1-9]\d*/,{timeout:9500});
  await expect(stage).toHaveAttribute("data-selected-orb-x",/-?\d+\.\d+/);
  await expect(stage).toHaveAttribute("data-track-visible","1");
  await page.waitForTimeout(3500); // evidence after the grid spreads, not an artificial still pose
  const fs=await import("node:fs");
  fs.mkdirSync("test-results/visuals",{recursive:true});
  await page.screenshot({path:"test-results/visuals/oval-three-quarter-"+testInfo.project.name+".png",fullPage:true});
});

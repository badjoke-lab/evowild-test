import { test, expect } from "@playwright/test";
test("P distance-phase trial tracks forward distance without changing S/E/A sprites", async ({page}) => {
  test.setTimeout(90000);
  const errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  await page.clock.install({time:new Date("2026-10-12T00:00:00Z")});
  await page.clock.pauseAt(new Date("2026-10-12T00:00:00Z"));
  await page.goto("/evowild-test/race-quality.html?selected=2&pStrideClock=distance");
  await expect(page.locator("#stage")).toHaveAttribute("data-run-sheets","ready");
  await page.clock.runFor(4600);
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-p-cadence-model","integrated-distance-trial");
  const observed=[];
  for(let k=0;k<28;k++){
    await page.clock.runFor(120);
    observed.push(await stage.evaluate(el=>({
      phase:Number(el.dataset.pRunPosition),
      distance:Number(el.dataset.selectedDistance),
      speed:Number(el.dataset.selectedSpeed),
      frame:Number(el.dataset.selectedRunFrame)
    })));
  }
  const length=Number(await stage.getAttribute("data-p-calibrated-cycle-metres"));
  expect(length).toBeGreaterThan(10);
  expect(length).toBeLessThan(20);
  const ratios=[];
  for(let i=1;i<observed.length;i++){
    const deltaPhase=observed[i].phase-observed[i-1].phase;
    const deltaDistance=observed[i].distance-observed[i-1].distance;
    if(deltaPhase>.01 && deltaDistance>.05)
      ratios.push(deltaDistance/(deltaPhase/6));
  }
  expect(ratios.length).toBeGreaterThan(20);
  const maxError=Math.max(...ratios.map(x=>Math.abs(x-length)));
  expect(maxError).toBeLessThan(.85);
  expect(new Set(observed.map(x=>x.frame)).size).toBeGreaterThan(5);
  expect(errors).toEqual([]);
  console.log("P_STRIDE_DISTANCE_TRIAL",JSON.stringify({calibratedMetres:length,
    maxCycleDistanceErrorMetres:maxError,speedRange:[Math.min(...observed.map(x=>x.speed)),
    Math.max(...observed.map(x=>x.speed))],sampleCount:observed.length,
    limitation:"This validates phase-distance clocking only. Actual sole pinning is NOT proven."}));
});

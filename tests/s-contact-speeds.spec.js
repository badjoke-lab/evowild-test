import {test,expect} from '@playwright/test';
import {summarizeContactRun} from '../src/s_sole_metrics.js';

test('all three S travel speeds retain actual sole contact with independently changing stride and cadence',async({page})=>{
 test.setTimeout(180000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
 const reports=[];
 for(const rate of [.5,1,1.5]){
  const trace=await page.evaluate(rate=>window.sRunReview.measureCycle(rate,240),rate),report=summarizeContactRun(trace);reports.push(report);
  expect(report.travelSpeed).toBeCloseTo(4*rate,7);
  for(const foot of report.feet){
   expect(foot.maxPenetration).toBeLessThan(.001);
   expect(foot.controllerStanceTime).toBeGreaterThan(.05);
   expect(foot.controllerStanceSlipForward).toBeLessThan(.001);
   expect(foot.controllerStanceSlipLateral).toBeLessThan(.001);
   expect(foot.maxReachError).toBeLessThan(.001);
   expect(foot.recoveryHeight).toBeGreaterThan(foot.name.startsWith('hind')?.44:.30);
   for(const [min,max] of foot.jointAngleRanges){expect(min).toBeGreaterThan(35);expect(max).toBeLessThan(178);}
  }
  // Exercise real browser animation, not only offline poses, at each rate.
  await page.evaluate(()=>window.sRunReview.setPhase(.1,'REAR_3_4'));await page.locator('#pause').click();
  const before=await page.evaluate(()=>window.sRunReview.sample());await page.waitForTimeout(400);const after=await page.evaluate(()=>window.sRunReview.sample());
  expect(after.time).toBeGreaterThan(before.time);expect(after.distance).toBeGreaterThan(before.distance);
  await page.locator('#pause').click();
 }
 expect(reports[2].stride/reports[0].stride).toBeCloseTo(Math.sqrt(3),6);
 expect(reports[2].cadence/reports[0].cadence).toBeCloseTo(Math.sqrt(3),6);
 expect(errors).toEqual([]);
});

import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile,summarizeProfile} from '../scripts/s_contact_profiles.mjs';

test('continuous acceleration, deceleration and abrupt commands preserve actual sole position and velocity',async({page})=>{
 test.setTimeout(180000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
 for(const profile of profiles){
  const trace=await page.evaluate(captureContactProfile,{profile});const summary=summarizeProfile(trace);
  expect(Math.abs(summary.travelIntegralError)).toBeLessThan(.005);expect(Math.abs(summary.cycleIntegralError)).toBeLessThan(.003);
  for(const f of summary.feet){
   expect(f.maxZeroTimeJump).toBeLessThan(.001);
   // 10 microsecond one-sided actual-mesh derivatives across command changes;
   // finite acceleration/noise is allowed, the former 5–8m/s jumps are not.
   expect(f.maxMeshVelocityResidual).toBeLessThan(.02);
   expect(f.stanceSlip).toBeLessThan(.001);expect(f.maxPenetration).toBeLessThan(.001);expect(f.maxReachError).toBeLessThan(.001);
   expect(f.maxSegmentLengthDrift).toBeLessThan(.00001);expect(f.jointAngleRange[0]).toBeGreaterThan(35);expect(f.jointAngleRange[1]).toBeLessThan(178);
   expect(f.recoveryHeight).toBeGreaterThan(f.name.startsWith('hind')?.44:.30);expect(f.contactTime).toBeGreaterThan(.03);
  }
  console.log('C2',JSON.stringify(summary));
 }
 expect(errors).toEqual([]);
});

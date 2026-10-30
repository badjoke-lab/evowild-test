import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';
import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';

test('D3-C authored scapula protects real fore/hind soles in motion',async({page})=>{
 test.setTimeout(300000);
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v1');
 await page.waitForFunction(()=>window.sRunReview?.footSample);
 const choices=[
  {name:'steady-0.5',phase:0,mode:'step',knots:[[0,.5],[1,.5]]},
  {name:'steady-1',phase:0,mode:'step',knots:[[0,1],[1,1]]},
  {name:'steady-1.5',phase:0,mode:'step',knots:[[0,1.5],[1,1.5]]},
  ...profiles.filter(p=>p.name?.startsWith('abrupt')).slice(0,2),
  ...profiles.filter(p=>p.name?.includes('acceleration')).slice(0,1)
 ];
 for(const profile of choices){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true});
  const r=summarizeToeProfile(trace);
  const metrics={profile:profile.name,feet:r.feet.map(f=>({
    name:f.name,velocity:f.maxMeshVelocityResidual,reach:f.maxReachError,
    ground:f.maxSupportPlaneError,slip:f.supportSlip,penetration:f.guardPenetration,
    jump:f.maxZeroTimeJump,recovery:f.recoveryHeight
  }))};
  console.log('D3C_SCAPULA_SOLE',JSON.stringify(metrics));
  for(const foot of r.feet){
   expect(foot.maxMeshVelocityResidual).toBeLessThan(.02);
   expect(foot.maxZeroTimeJump).toBeLessThan(.001);
   expect(foot.guardPenetration).toBeLessThan(.001);
   expect(foot.maxReachError).toBeLessThan(.001);
   expect(foot.supportSlip).toBeLessThan(.001);
   expect(foot.maxSupportPlaneError).toBeLessThan(.001);
   expect(foot.recoveryHeight).toBeGreaterThan(foot.name.startsWith('hind')?.44:.30);
  }
 }
});
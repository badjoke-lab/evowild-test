import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';
import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';
const base='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=';
test('D3 push-v4 flex stays local and scales with simulated speed',async({page})=>{
 test.setTimeout(120000);
 const samples={};
 for(const variant of ['push-v3','push-v4']){
  await page.goto(base+variant);await page.waitForFunction(()=>window.sRunReview?.bodyVertexIds?.length>0);
  samples[variant]=await page.evaluate(()=>{
   window.requestAnimationFrame=()=>0;
   const a=window.sRunReview,points={};
   for(const rate of [.5,1,1.5])for(const phase of [.12,.34,.56,.64]){
    a.setRate(rate);a.setPhase(phase,'SIDE',false);
    const pelvis=a.bodySample().find(b=>b.name==='pelvis');
    const distance=a.sample().distance;
    points[rate+'@'+phase]={q:pelvis.quaternion,mesh:a.probe(a.bodyVertexIds).map(p=>[p[0],p[1],p[2]-distance])};
   }
   return points;
  });
 }
 const ang=(a,b)=>2*Math.acos(Math.min(1,Math.abs(a.reduce((sum,x,i)=>sum+x*b[i],0))))*180/Math.PI;
 const delta=(a,b)=>Math.max(...a.map((p,i)=>Math.hypot(...p.map((x,j)=>x-b[i][j]))));
 for(const rate of [.5,1,1.5])for(const phase of [.12,.56,.64]){
  const k=rate+'@'+phase;
  expect(delta(samples['push-v3'][k].mesh,samples['push-v4'][k].mesh)).toBeLessThan(.00001);
 }
 const slow=ang(samples['push-v3']['0.5@0.34'].q,samples['push-v4']['0.5@0.34'].q);
 const fast=ang(samples['push-v3']['1.5@0.34'].q,samples['push-v4']['1.5@0.34'].q);
 const bodyShift=delta(samples['push-v3']['1.5@0.34'].mesh,samples['push-v4']['1.5@0.34'].mesh);
 console.log('D3_FLEX_COMPARE',JSON.stringify({slowPelvisDegrees:slow,fastPelvisDegrees:fast,fastBodyShiftMeters:bodyShift}));
 expect(slow).toBeGreaterThan(1);
 expect(fast).toBeGreaterThan(slow+2);
 expect(bodyShift).toBeLessThan(.15);
});
test('D3 push-v4 keeps physical sole contact and integrated rate changes',async({page})=>{
 test.setTimeout(240000);
 await page.goto(base+'push-v4');await page.waitForFunction(()=>window.sRunReview);
 const candidates=[{name:'steady-0.5',phase:0,mode:'step',knots:[[0,.5],[1,.5]]},
  {name:'steady-1.5',phase:0,mode:'step',knots:[[0,1.5],[1,1.5]]},
  ...profiles.filter(p=>p.name?.startsWith('abrupt')).slice(0,2)];
 for(const profile of candidates){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true});
  const result=summarizeToeProfile(trace);
  for(const foot of result.feet){
   expect(foot.maxZeroTimeJump).toBeLessThan(.001);
   expect(foot.maxMeshVelocityResidual).toBeLessThan(.02);
   expect(foot.guardPenetration).toBeLessThan(.001);
   expect(foot.maxReachError).toBeLessThan(.001);
   expect(foot.supportSlip).toBeLessThan(.001);
   expect(foot.maxSupportPlaneError).toBeLessThan(.001);
   expect(foot.recoveryHeight).toBeGreaterThan(foot.name.startsWith('hind')?.44:.30);
  }
  console.log('D3_FLEX_CONTACT',JSON.stringify({profile:profile.name,feet:result.feet.map(f=>({name:f.name,reach:f.maxReachError,zeroJump:f.maxZeroTimeJump,slip:f.supportSlip,clearance:f.maxSupportPlaneError}))}));
 }
});

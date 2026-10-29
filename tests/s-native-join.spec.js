import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';
import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';

const base='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=';

// A review-only comparison, not a declaration that the motion is approved.
test('native phase .64 join reduces measured body-mesh velocity corner',async({page})=>{
 test.setTimeout(120000);
 const results=[];
 for(const mode of ['push-v2','push-v3']){
  await page.goto(base+mode);
  await page.waitForFunction(()=>window.sRunReview?.bodyVertexIds?.length>0);
  const data=await page.evaluate(()=>{
   window.requestAnimationFrame=()=>0;
   const a=window.sRunReview,ids=a.bodyVertexIds;
   const sample=phase=>{
    a.setRate(1);a.setPhase(phase,'SIDE',false);
    const distance=a.sample().distance;
    return a.probe(ids).map(p=>p.map((x,i)=>i===2?x-distance:x));
   };
   const maxDiff=(u,v)=>Math.max(...u.map((p,j)=>Math.hypot(...p.map((x,i)=>x-v[j][i]))));
   const scan=[.635,.638,.639,.64,.641,.642,.645];
   const h=.0001,dt=h/2.4;
   const corners=scan.map(phase=>{
    const l=sample(phase-h),m=sample(phase),r=sample(phase+h);
    const residual=Math.max(...m.map((p,j)=>Math.hypot(...p.map((x,i)=>(r[j][i]-2*x+l[j][i])/dt))));
    return {phase,residual};
   });
   const exterior=[.52,.59,.62,.68,.70,.78].map(phase=>({phase,vertices:sample(phase)}));
   const center=sample(.64);
   return {corners,exterior,center,vertices:ids.length};
  });
  results.push({mode,...data});
 }
 const [before,after]=results;
 const worst=s=>Math.max(...s.corners.map(c=>c.residual));
 console.log('D2-D native join diagnostic',JSON.stringify({before:before.corners,after:after.corners,worstBefore:worst(before),worstAfter:worst(after)}));
 expect(after.vertices).toBe(before.vertices);
 for(let i=0;i<before.exterior.length;i++){
  const a=after.exterior[i],b=before.exterior[i];
  expect(a.phase).toBe(b.phase);
  const diff=Math.max(...a.vertices.map((p,j)=>Math.hypot(...p.map((x,k)=>x-b.vertices[j][k]))));
  expect(diff).toBeLessThan(.00001);
 }
 const maxChanged=Math.max(...after.center.map((p,j)=>Math.hypot(...p.map((x,k)=>x-before.center[j][k]))));
 console.log('D2-D center deformation',maxChanged);
 // Guard against disguising a corner through a large unrelated body shift.
 expect(maxChanged).toBeLessThan(.05);
 expect(worst(after)).toBeLessThan(worst(before));
});

test('experimental D2-D join preserves contact at 1x and abrupt rate changes',async({page})=>{
 test.setTimeout(240000);
 await page.goto(base+'push-v3');await page.waitForFunction(()=>window.sRunReview);
 const candidates=[{name:'steady-1',phase:0,mode:'step',knots:[[0,1],[1,1]]},...profiles.filter(p=>p.name?.startsWith('abrupt')).slice(0,2)];
 expect(candidates.length).toBeGreaterThan(1);
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
  console.log('D2-D contact',JSON.stringify({profile:profile.name,feet:result.feet}));
 }
});

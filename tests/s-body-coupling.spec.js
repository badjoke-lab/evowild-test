import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';
import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';

test('rolling support preserves mesh contact across steady speeds and all C2 speed profiles',async({page})=>{
 test.setTimeout(240000);await page.goto('/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v2&body=push-v1');await page.waitForFunction(()=>window.sRunReview);
 const cases=[...[.5,1,1.5].map(rate=>({name:'steady-'+rate,phase:0,mode:'step',knots:[[0,rate],[1,rate]]})),...profiles];
 for(const profile of cases){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true}),s=summarizeToeProfile(trace);
  for(const f of s.feet){
   expect(f.maxZeroTimeJump).toBeLessThan(.001);expect(f.maxMeshVelocityResidual).toBeLessThan(.02);
   expect(f.supportSlip).toBeLessThan(.001);expect(f.maxSupportPlaneError).toBeLessThan(.001);expect(f.guardPenetration).toBeLessThan(.001);expect(f.maxReachError).toBeLessThan(.001);
   expect(f.jointAngleRange[0]).toBeGreaterThan(35);expect(f.jointAngleRange[1]).toBeLessThan(178);expect(f.maxSegmentLengthDrift).toBeLessThan(.00001);
   expect(f.recoveryHeight).toBeGreaterThan(f.name.startsWith('hind')?.44:.30);
   expect(f.rearRise).toBeGreaterThan(f.name.startsWith('hind')?.03:.04);expect(f.pitchRange[1]-f.pitchRange[0]).toBeGreaterThan(f.name.startsWith('hind')?24:18);
   expect(f.flatTime).toBeGreaterThan(.02);expect(f.toeTime).toBeGreaterThan(.02);
   // Old whole-patch movement is retained as evidence, never relabelled as
   // supporting-point slip or forced below its old flat-contact threshold.
   expect(f.legacyAllPatchMovement).toBeGreaterThan(.005);
  }
  console.log('D2-B',JSON.stringify({profile:profile.name,feet:s.feet}));
 }
});

test('support-vertex changes and lift-off have continuous actual mesh motion and zero-speed freeze',async({page})=>{
 test.setTimeout(120000);await page.goto('/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v2&body=push-v1');await page.waitForFunction(()=>window.sRunReview);
 const results=await page.evaluate(()=>{
  const a=window.sRunReview,offsets=[.64,.72,.15,.24],out=[],eps=1e-5,cadence=2.4;
  const diff=(p,q)=>Math.max(...p.map((s,i)=>Math.hypot(...s.map((x,j)=>x-q[i][j]))));
  for(let foot=0;foot<4;foot++){
   const stance=foot<2?.17:.23,flat=a.rollDescriptors[foot].flatEnd,knots=a.rollDescriptors[foot].segments.map(s=>flat*stance+(1-flat)*stance*s.to);
   for(const boundary of [...knots,stance,1]){
    a.setRate(1);a.setPhase(offsets[foot]+boundary-cadence*eps,'SIDE');const p=a.probe(a.footSurfaces[foot].ids);
    a.step(eps);const q=a.probe(a.footSurfaces[foot].ids);a.setRate(1.5);a.step(0);const q2=a.probe(a.footSurfaces[foot].ids);
    a.step(eps);const r=a.probe(a.footSurfaces[foot].ids);
    const velocityResidual=Math.max(...q.map((v,i)=>Math.hypot(...v.map((x,j)=>(r[i][j]-q2[i][j])/eps-(x-p[i][j])/eps))));
    a.setRate(0);a.step(0);const frozen=a.probe(a.footSurfaces[foot].ids);a.step(.3);const still=a.probe(a.footSurfaces[foot].ids);
    out.push({foot,boundary,zeroJump:diff(q,q2),velocityResidual,freeze:diff(frozen,still)});
   }
  }
  return out;
 });
 for(const r of results){expect(r.zeroJump).toBeLessThan(.001);expect(r.velocityResidual).toBeLessThan(.02);expect(r.freeze).toBeLessThan(1e-7);}
 console.log('D2-B boundaries',JSON.stringify(results));
});


test('body coupling retimes the native seven-bone shape and keeps protected skinned vertices',async({page})=>{
 const samples=[];
 for(const coupled of [false,true]){
  await page.goto('/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v2'+(coupled?'&body=push-v1':''));await page.waitForFunction(()=>window.sRunReview?.bodySample);
  samples.push(await page.evaluate(coupled=>{
   window.requestAnimationFrame=()=>0;const a=window.sRunReview;a.setRate(1);
   return [0,.2,.24,.35,.43,.7,.99].map(p=>{a.setPhase(p+(coupled||p<.18||p>.44?0:.25),'SIDE',false);const d=a.sample().distance;return {phase:p,lead:a.bodyPhaseLead,body:a.bodySample().map(b=>({...b,position:b.position.map((x,i)=>x-(i===2?d:0))})),points:a.probe(a.bodyVertexIds).map(p=>p.map((x,i)=>x-(i===2?d:0)))};});
  },coupled));
 }
 let maxShapeError=0;
 samples[0].forEach((b,i)=>{const a=samples[1][i];expect(a.lead).toBe(.25);a.points.forEach((p,k)=>{const d=Math.hypot(...p.map((v,j)=>v-b.points[k][j]));maxShapeError=Math.max(maxShapeError,d);expect(d).toBeLessThan(.00001);});a.body.forEach((bone,k)=>{bone.quaternion.forEach((v,j)=>expect(Math.abs(v-b.body[k].quaternion[j])).toBeLessThan(.00001));});});
 console.log('D2-B protected native shape',JSON.stringify({maxShapeError,samples}));
});

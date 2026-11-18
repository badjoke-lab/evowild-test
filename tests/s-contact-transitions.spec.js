import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import crypto from 'node:crypto';

test('S contact anchors survive fore/hind speed changes, zero elapsed time, freeze and swing replanning',async({page})=>{
 test.setTimeout(120000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
 const report=await page.evaluate(()=>{
  const api=window.sRunReview;
  const difference=(a,b)=>Math.max(...a.soles.flatMap((f,i)=>f.points.map((p,j)=>Math.hypot(...p.map((x,k)=>x-b.soles[i].points[j][k])))));
  const cases=[];
  for(const phase of [.2,.7]){
   api.setRate(.5);api.setPhase(phase,'REAR_3_4');const before=api.motionSample();
   api.setRate(1.5);api.advance(0);const after=api.motionSample();
   const r={phase,zeroJump:difference(before,after),maxPenetration:0,maxStanceSlip:0,maxReachError:0,minAngle:180,maxAngle:0,stanceCounts:[0,0,0,0],freezeJump:0};
   let prev=after;
   for(let j=0;j<360;j++){
    if(j===120)api.setRate(.5);
    api.step(1/240);const curr=api.motionSample();
    curr.soles.forEach((f,i)=>{
     r.maxPenetration=Math.max(r.maxPenetration,-f.minY);const l=curr.contact.limbs[i],p=prev.contact.limbs[i];
     r.maxReachError=Math.max(r.maxReachError,l.reachError);
     r.minAngle=Math.min(r.minAngle,...l.jointAngles);r.maxAngle=Math.max(r.maxAngle,...l.jointAngles);
     if(l.anchor&&p.anchor&&l.touchdowns===p.touchdowns){r.stanceCounts[i]++;for(let k=0;k<f.points.length;k++)r.maxStanceSlip=Math.max(r.maxStanceSlip,Math.hypot(...f.points[k].map((x,d)=>x-prev.soles[i].points[k][d])));}
    });prev=curr;
   }
   api.setRate(0);api.advance(0);const frozen=api.motionSample();api.advance(.5);const still=api.motionSample();
   r.freezeJump=difference(frozen,still);r.freezeTime=still.time-frozen.time;r.freezeDistance=still.distance-frozen.distance;
   // A diagnostic seek is explicit and reproducible; normal updates never seek.
   api.setRate(.5);api.setPhase(phase,'SIDE');const seek1=api.motionSample();api.setPhase(phase,'SIDE');r.seekDifference=difference(seek1,api.motionSample());
   cases.push(r);
  }
  return cases;
 });
 for(const r of report){
  expect(r.zeroJump).toBeLessThan(.001);expect(r.freezeJump).toBeLessThan(1e-7);expect(r.freezeTime).toBe(0);expect(r.freezeDistance).toBe(0);expect(r.seekDifference).toBeLessThan(1e-7);
  expect(r.maxPenetration).toBeLessThan(.001);expect(r.maxStanceSlip).toBeLessThan(.001);expect(r.maxReachError).toBeLessThan(.001);
  expect(r.minAngle).toBeGreaterThan(35);expect(r.maxAngle).toBeLessThan(178);for(const n of r.stanceCounts)expect(n).toBeGreaterThan(10);
 }
 expect(errors).toEqual([]);
 expect(crypto.createHash('sha256').update(fs.readFileSync('public/models/evowild-s/review/focus-contact-v3.glb')).digest('hex')).toBe('78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f');
 console.log('C1 actual-mesh results',JSON.stringify(report));
});

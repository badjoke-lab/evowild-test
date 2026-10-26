import {test,expect} from '@playwright/test';
import {summarizeSoles,summarizeContactRun} from '../src/s_sole_metrics.js';

test('sole metrics distinguish a planted patch from sliding penetrating geometry',()=>{
 const frames=sliding=>[0,1,2].map(i=>({t:i*.1,distance:i*.4,soles:[{name:'foot',minY:-.01,lowest:[0,-.01,0],points:[[sliding?i*.03:0,-.01,sliding?i*.1:0],[sliding?i*.03+.05:.05,0,sliding?i*.1:0]]}]}));
 const fixed=summarizeSoles(frames(false)).feet[0],moving=summarizeSoles(frames(true)).feet[0];
 expect(summarizeContactRun({frames:frames(false),cycleDuration:.2}).feet[0].controllerStanceTime).toBeNull();
 expect(fixed.supportSlipForward).toBe(0);expect(fixed.supportSlipLateral).toBe(0);
 expect(moving.supportSlipForward).toBeCloseTo(.2);expect(moving.supportSlipLateral).toBeCloseTo(.06);
 expect(moving.maxPenetration).toBeCloseTo(.01);expect(moving.supportCandidateTime).toBeCloseTo(.2);
});

test('actual sole trace agrees with independently probed SkinnedMesh vertex IDs',async({page})=>{
 test.setTimeout(60000);
 await page.goto('/evowild-test/s-run-review.html?rig=hind-v2');await page.waitForFunction(()=>window.sRunReview);
 const trace=await page.evaluate(()=>window.sRunReview.measureCycle(1,240));
 expect(trace.frames).toHaveLength(241);expect(trace.groundY).toBe(0);
 await page.evaluate(()=>window.sRunReview.setPhase(.5,'LOW'));
 for(let foot=0;foot<4;foot++){
   const patch=trace.patches[foot];expect(patch.indices.length).toBeGreaterThan(3);
   const actual=await page.evaluate(ids=>window.sRunReview.probe(ids),patch.indices);
   const expected=trace.frames[120].soles[foot];
   for(let i=0;i<actual.length;i++)expect(Math.hypot(...actual[i].map((n,j)=>n-expected.points[i][j]))).toBeLessThan(1e-7);
   expect(expected.minY).toBeCloseTo(Math.min(...actual.map(p=>p[1])),7);
 }
});

import {test,expect} from '@playwright/test';
import fs from 'node:fs';
const report=JSON.parse(fs.readFileSync('docs/2p5d/evidence/20261026-s-hind-fit/asset-report.json'));

test('hind fit retains non-hind skin motion and geometry while articulating toe chains',async({page},testInfo)=>{
  test.setTimeout(120000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const samples=[];
  for(const rig of ['bind-v1','hind-v2']){
    await page.goto('/evowild-test/s-run-review.html?rig='+rig);
    await page.waitForFunction(()=>window.sRunReview);
    const phases=[];
    for(const phase of [0,.25,.5,.75]){
      const state=await page.evaluate(p=>window.sRunReview.setPhase(p,'REAR_3_4'),phase);
      const points=await page.evaluate(ids=>window.sRunReview.probe(ids),report.protectedProbeIndices);
      phases.push({state,points});
    }
    samples.push(phases);
  }
  for(let phase=0;phase<4;phase++)for(let point=0;point<samples[0][phase].points.length;point++){
    const a=samples[0][phase].points[point],b=samples[1][phase].points[point];
    expect(Math.hypot(...a.map((v,i)=>v-b[i]))).toBeLessThan(.00001);
  }
  expect(samples[1][0].state.bones).toBe(21);
  for(const foot of samples[1][0].state.feet.filter(f=>f.name.startsWith('hind_')))expect(foot.weightBone).toMatch(/_toe$/);
  const a=samples[1][0].state.feet[2],b=samples[1][1].state.feet[2];
  expect(Math.abs(a.y-b.y)).toBeGreaterThan(.01);
  await page.evaluate(()=>window.sRunReview.setPhase(.25,'REAR_3_4'));
  await page.screenshot({path:testInfo.outputPath('hind-v2.png')});
  expect(errors).toEqual([]);
});

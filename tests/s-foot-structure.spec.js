import {test,expect} from '@playwright/test';

test('S distal contact descriptors use actual rigid mesh vertices and distinct fore/hind terminal joints',async({page})=>{
 test.setTimeout(90000);await page.goto('/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
 const results=await page.evaluate(()=>{
  const a=window.sRunReview;a.setRate(1);a.setPhase(.32,'SIDE');
  return a.footSurfaces.map((s,i)=>{
   a.setPhase(.32,'SIDE');const before=a.footSample()[i],after=a.probeFootRotation(i,35),probed=a.probe(s.ids);
   const separation=p=>Math.hypot(...p.at(-1).map((x,d)=>x-p[0][d]));
   return {name:s.name,terminal:s.terminal,weight:s.minTerminalWeight,containsSole:a.solePatches[i].indices.every(id=>s.ids.includes(id)),pitchChange:before.pitchDegrees-after.pitchDegrees,lengthDrift:Math.abs(separation(before.points)-separation(after.points)),probeError:Math.max(...probed.map((p,k)=>Math.hypot(...p.map((x,d)=>x-after.points[k][d])))),rear:s.rearIds.length,front:s.frontIds.length};
  });
 });
 for(const r of results){expect(r.weight).toBeGreaterThan(.999999);expect(r.containsSole).toBe(true);expect(r.pitchChange).toBeCloseTo(35,4);expect(r.lengthDrift).toBeLessThan(1e-6);expect(r.probeError).toBeLessThan(1e-7);expect(r.rear).toBeGreaterThan(0);expect(r.front).toBeGreaterThan(0);expect(r.terminal.endsWith(r.name.startsWith('hind')?'_toe':'_foot')).toBe(true);}
});

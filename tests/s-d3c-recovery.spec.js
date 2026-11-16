import {test,expect} from '@playwright/test';
test('fore recovery ablation observes actual skin and restores unchanged v2 pose',async({page})=>{
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v2');await page.waitForFunction(()=>window.sRunReview);
 const r=await page.evaluate(()=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview; s.setPhase(.307,'SIDE',false);const ids=Array.from({length:310},(_,i)=>i*125),before=s.probe(ids),audit=s.recoveryAudit(),after=s.probe(ids);
  return {restore:Math.max(...before.map((p,i)=>Math.hypot(...p.map((v,j)=>v-after[i][j])))),double:Math.max(...audit.first.fore.map((f,i)=>Math.hypot(...f.centroid.map((v,j)=>v-audit.zeroSecond.fore[i].centroid[j])))),fold:audit.full.fore.map((f,i)=>audit.first.fore[i].elbowDegrees-f.elbowDegrees),nearest:audit.full.nearestSurfaceDistance};});
 console.log('FORE_AUDIT',r);expect(r.restore).toBeLessThan(1e-6);expect(r.double).toBeLessThan(1e-6);expect(r.fold[1]).toBeGreaterThan(25);expect(r.nearest).toBeGreaterThan(.1);
});

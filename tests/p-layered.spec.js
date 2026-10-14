import {test, expect} from '@playwright/test';

test('P layered trial keeps four independent feet planted, pauses and resets in an 18-runner race', async ({page})=>{
  test.setTimeout(45000);
  const time=new Date('2026-10-12T00:00:00Z');
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.clock.install({time});await page.clock.pauseAt(time);
  await page.goto('/evowild-test/race-quality.html?selected=2&pRig=1&pRigReview=1');
  const stage=page.locator('#stage');
  await expect(stage).toHaveAttribute('data-run-sheets','ready');
  await expect(stage).toHaveAttribute('data-p-rig-status','ready');
  await page.clock.runFor(4600);
  // Sample the actual renderer inside the page. Every animation frame is sampled on both devices. Clock/evaluate pairs
  // plus thousands of traced expect calls previously exhausted CI's 90s.
  await page.evaluate(()=>{
    window.__pLayeredSamples=[];let last=-Infinity;
    const collect=()=>{
      const selected=window.__pRigReview;
      if(selected&&selected.time>last){
        last=selected.time;
        window.__pLayeredSamples.push(structuredClone({selected,field:Object.values(window.__pRigField)}));
      }
      requestAnimationFrame(collect);
    };
    requestAnimationFrame(collect);
  });
  await page.clock.runFor(3000);
  const samples=await page.evaluate(()=>window.__pLayeredSamples);
  await expect(stage).toHaveAttribute('data-field-size','18');
  await expect(stage).toHaveAttribute('data-visible-racers','18');
  await expect(stage).toHaveAttribute('data-p-renderer','layered-world-stance');
  expect(samples.at(-1).selected.cycle-samples[0].selected.cycle).toBeGreaterThan(3);
  expect(samples.length).toBeGreaterThan(60);
  let contacts=0,maxAnchorDrift=0,maxReach=0,maxBoneError=0,maxCompression=0,maxSink=0;
  const footSets=new Set(),runnerCounts=new Set();
  for(let i=1;i<samples.length;i++){
    const {selected,field}=samples[i];
    footSets.add(selected.feet.map(f=>f.id).sort().join(','));runnerCounts.add(field.length);
    maxCompression=Math.max(maxCompression,...field.map(r=>r.bodyOffset));
    maxSink=Math.max(maxSink,...field.map(r=>r.bodySink));
    for(const runner of field)for(const foot of runner.feet){
      maxReach=Math.max(maxReach,foot.reachError);maxBoneError=Math.max(maxBoneError,foot.boneLengthError);
      const previous=samples[i-1].field.find(r=>r.id===runner.id)?.feet.find(f=>f.id===foot.id);
      if(previous&&foot.stance&&previous.stance&&foot.contactId===previous.contactId){
        contacts++;
        maxAnchorDrift=Math.max(maxAnchorDrift,Math.abs(foot.worldX-previous.worldX),Math.abs(foot.worldLane-previous.worldLane));
      }
    }
  }
  expect([...footSets]).toEqual(['fore-far,fore-near,hind-far,hind-near']);
  expect([...runnerCounts]).toEqual([5]);
  expect(maxAnchorDrift).toBe(0);expect(maxReach).toBeLessThan(.000001);
  expect(maxBoneError).toBeLessThan(.000001);
  expect(maxCompression).toBeLessThanOrEqual(12);expect(maxSink).toBeLessThanOrEqual(20);
  expect(samples.some(s=>s.selected.feet.every(f=>!f.stance))).toBe(true);
  expect(contacts).toBeGreaterThan(20);
  // Dispatch the control under the intentionally paused browser clock; a
  // pointer click's animation-frame stability wait cannot advance that clock.
  await page.locator('#pause').evaluate(button=>button.click());
  const paused=await page.evaluate(()=>window.__pRigReview);
  await page.clock.runFor(700);
  const after=await page.evaluate(()=>window.__pRigReview);
  expect(after.cycle).toBe(paused.cycle);
  // The existing camera may finish its easing while simulation is paused.
  // World contacts and the actual local leg geometry must remain unchanged.
  for(const foot of after.feet){
    const before=paused.feet.find(f=>f.id===foot.id);
    expect(foot.worldX).toBe(before.worldX);expect(foot.worldLane).toBe(before.worldLane);
    expect(foot.stance).toBe(before.stance);expect(foot.contactId).toBe(before.contactId);
    for(const joint of ['hip','knee','ankle'])for(const axis of ['x','y'])expect(foot[joint][axis]).toBeCloseTo(before[joint][axis],7);
  }
  await page.locator('#reset').evaluate(button=>button.click());await page.clock.runFor(32);
  const reset=await page.evaluate(()=>window.__pRigReview);
  expect(reset.cycle).toBeLessThan(samples[0].selected.cycle);
  expect(reset.feet.every(f=>f.contactId===0)).toBe(true);
  expect(errors).toEqual([]);
});

import {test, expect} from '@playwright/test';

test('P layered trial keeps four independent feet planted, pauses and resets in an 18-runner race', async ({page})=>{
  test.setTimeout(90000);
  const time=new Date('2026-10-12T00:00:00Z');
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.clock.install({time});await page.clock.pauseAt(time);
  await page.goto('/evowild-test/race-quality.html?selected=2&pRig=1&pRigReview=1');
  const stage=page.locator('#stage');
  await expect(stage).toHaveAttribute('data-run-sheets','ready');
  await expect(stage).toHaveAttribute('data-p-rig-status','ready');
  await page.clock.runFor(4600);
  const samples=[];
  for(let i=0;i<90;i++){
    await page.clock.runFor(33);
    samples.push(await page.evaluate(()=>({selected:window.__pRigReview,field:Object.values(window.__pRigField)})));
  }
  await expect(stage).toHaveAttribute('data-field-size','18');
  await expect(stage).toHaveAttribute('data-visible-racers','18');
  await expect(stage).toHaveAttribute('data-p-renderer','layered-world-stance');
  expect(samples.at(-1).selected.cycle-samples[0].selected.cycle).toBeGreaterThan(3);
  let contacts=0;
  for(let i=1;i<samples.length;i++){
    const {selected,field}=samples[i];
    expect(selected.feet.map(f=>f.id).sort()).toEqual(['fore-far','fore-near','hind-far','hind-near']);
    expect(field.length).toBeGreaterThan(1);
    for(const runner of field)for(const foot of runner.feet){
      expect(foot.reachError).toBeLessThan(.001);
      expect(foot.boneLengthError).toBeLessThan(.000001);
    }
    for(const foot of selected.feet){
      const previous=samples[i-1].selected.feet.find(f=>f.id===foot.id);
      if(foot.stance&&previous.stance&&foot.contactId===previous.contactId){
        contacts++;
        expect(foot.worldX).toBe(previous.worldX);
        expect(foot.worldLane).toBe(previous.worldLane);
      }
    }
  }
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

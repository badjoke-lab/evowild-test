import {test, expect} from '@playwright/test';

test('canonical S native clip runs in four views and scales/freeze with speed', async ({page}) => {
  test.setTimeout(60000);
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const loaded=[];
  page.on('response',r=>{if(r.url().endsWith('.glb'))loaded.push(r.url());});
  await page.goto('/evowild-test/s-run-review.html');
  await page.waitForFunction(()=>window.sRunReview);
  expect(loaded).toHaveLength(1);
  expect(loaded[0]).toContain('/models/evowild-s/focus-rigged-v5.glb');
  const start=await page.evaluate(()=>window.sRunReview.sample());
  await expect.poll(()=>page.evaluate(()=>window.sRunReview.sample().time)).toBeGreaterThan(start.time+.05);
  const a=await page.evaluate(()=>window.sRunReview.setPhase(0,'SIDE'));
  const b=await page.evaluate(()=>window.sRunReview.setPhase(.5,'SIDE'));
  expect(a.clip).toBe('EvoWild_S_Run_V5');
  expect(a.bones).toBe(19);
  expect(a.vertices).toBe(38813);
  // Native skin deformation must occur, beyond whole-model translation.
  expect(Math.max(...a.feet.map((f,i)=>Math.abs(f.y-b.feet[i].y)))).toBeGreaterThan(.02);
  for(const view of ['SIDE','CHASE','LOW','REAR_3_4']){
    await page.selectOption('#camera',view);
    await expect(page.locator('#status')).toContainText(view);
    await expect(page.locator('canvas')).toBeVisible();
  }
  await page.selectOption('#speed','0');
  const frozen=await page.evaluate(()=>window.sRunReview.sample());
  const still=await page.evaluate(()=>window.sRunReview.advance(.2));
  expect(still.time).toBe(frozen.time);expect(still.distance).toBe(frozen.distance);expect(still.feet).toEqual(frozen.feet);
  const deltas=[];
  for(const rate of ['0.5','1.5']){
    await page.selectOption('#speed',rate);
    const before=await page.evaluate(()=>window.sRunReview.setPhase(0,'REAR_3_4'));
    const after=await page.evaluate(()=>window.sRunReview.advance(.2));
    deltas.push({time:after.time-before.time,distance:after.distance-before.distance});
  }
  expect(deltas[1].time/deltas[0].time).toBeCloseTo(3);
  expect(deltas[1].distance/deltas[0].distance).toBeCloseTo(3);
  await expect(page.locator('#error')).toBeEmpty();expect(errors).toEqual([]);
  // This proves runtime plumbing, not gait/contact quality; visual verdict stays REVISE.
});

import {test,expect} from '@playwright/test';
const u='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5';

async function sample(page,variant,phase,rate=1){
 await page.goto(u+variant);
 await page.waitForFunction(()=>window.sRunReview?.probe);
 return page.evaluate(({phase,rate})=>{
  const s=window.sRunReview;
  window.requestAnimationFrame=()=>0;
  s.setRate(rate);s.setPhase(phase,'SIDE',false);
  const ids=Array.from({length:310},(_,i)=>i*125).filter(x=>x<38813);
  const m=s.motionSample();
  return {bones:s.sample().bones,vertices:s.probe(ids),
   contact:m.contact.limbs.map(l=>({name:l.name,anchor:l.anchor,reachError:l.reachError})),
   sole:m.soles};
 },{phase,rate});
}
const diff=(a,b)=>Math.max(...a.map((p,i)=>Math.hypot(...p.map((v,j)=>v-b[i][j]))));
test('D3-C real scapula bone skinning preserves original animation when zeroed',async({page})=>{
 test.setTimeout(120000);
 for(const phase of [0,.20,.32,.64,.75,.90]){
  const old=await sample(page,'',phase);
  const neutral=await sample(page,'&shoulder=neutral-v1',phase);
  expect(neutral.bones).toBe(23);
  expect(old.bones).toBe(21);
  const drift=diff(old.vertices,neutral.vertices);
  console.log('D3C_NEUTRAL',JSON.stringify({phase,drift}));
  expect(drift).toBeLessThan(.001);
  for(let i=0;i<4;i++){
   expect(neutral.contact[i].reachError).toBeLessThan(.001);
   if(old.contact[i].anchor&&neutral.contact[i].anchor)
    expect(diff([old.contact[i].anchor],[neutral.contact[i].anchor])).toBeLessThan(.001);
  }
 }
});
test('D3-C animated scapulas move actual skin, not only controller or foot targets',async({page})=>{
 test.setTimeout(120000);
 let max=0;
 for(const phase of [.20,.32,.64,.75,.90]){
  const neutral=await sample(page,'&shoulder=neutral-v1',phase);
  const active=await sample(page,'&shoulder=authored-v1',phase);
  const displacement=diff(neutral.vertices,active.vertices);
  max=Math.max(max,displacement);
  console.log('D3C_ACTUAL_SKIN_DELTA',JSON.stringify({phase,displacement}));
  expect(displacement).toBeLessThan(.2);
  for(const limb of active.contact)expect(limb.reachError).toBeLessThan(.001);
 }
 expect(max).toBeGreaterThan(.001);
});

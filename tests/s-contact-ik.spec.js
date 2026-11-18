import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {summarizeSoles} from '../src/s_sole_metrics.js';
function glb(path){const b=fs.readFileSync(path),n=b.readUInt32LE(12);return {d:JSON.parse(b.subarray(20,20+n)),b:b.subarray(28+n)};}
function bytes(g,i){const a=g.d.accessors[i],v=g.d.bufferViews[a.bufferView];return g.b.subarray(v.byteOffset+(a.byteOffset||0),v.byteOffset+v.byteLength);}
test('contact candidate preserves v2 geometry, all rest joints and native clip bytes',()=>{
 const path='public/models/evowild-s/review/',a=glb(path+'focus-hind-fit-v2.glb'),b=glb(path+'focus-contact-v3.glb');
 expect(crypto.createHash('sha256').update(fs.readFileSync(path+'focus-hind-fit-v2.glb')).digest('hex')).toBe('efa804ea4c3e2a2d272918e6982da12a365f1759140f50fa6d3f586c5fd2bede');
 expect(b.d.nodes).toEqual(a.d.nodes);expect(b.d.skins).toEqual(a.d.skins);
 const aa=a.d.meshes[0].primitives[0];for(const i of [aa.attributes.POSITION,aa.attributes.NORMAL,aa.indices])expect(bytes(b,i).equals(bytes(a,i))).toBe(true);
 for(const anim of a.d.animations)for(const s of anim.samplers)for(const i of [s.input,s.output])expect(bytes(b,i).equals(bytes(a,i))).toBe(true);
});
test('actual contact IK plants soles, lifts recovery and avoids inverted knee solutions',async({page},testInfo)=>{
 test.setTimeout(120000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
 const trace=await page.evaluate(()=>window.sRunReview.measureCycle(1,240));const summary=summarizeSoles(trace.frames);
 for(let i=0;i<4;i++){
  const f=summary.feet[i];expect(f.maxPenetration).toBeLessThan(.001);expect(f.supportSlipForward).toBeLessThan(.08);expect(f.supportSlipLateral).toBeLessThan(.001);
  expect(f.recoveryHeight).toBeGreaterThan(i<2?.30:.44);
  let stanceSteps=0;
  for(let j=1;j<trace.frames.length;j++){
   const curr=trace.frames[j],prev=trace.frames[j-1],l=curr.contact.limbs[i];
   expect(l.reachError).toBeLessThan(.012);
   for(const angle of l.jointAngles){expect(angle).toBeGreaterThan(35);expect(angle).toBeLessThan(178);}
   if(['CONTACT','PUSH'].includes(l.stage)&&['CONTACT','PUSH'].includes(prev.contact.limbs[i].stage)){
    stanceSteps++;expect(Math.abs(curr.soles[i].minY)).toBeLessThan(.001);
    for(let k=0;k<curr.soles[i].points.length;k++)expect(Math.hypot(...curr.soles[i].points[k].map((x,d)=>x-prev.soles[i].points[k][d]))).toBeLessThan(.001);
   }
  }
  expect(stanceSteps).toBeGreaterThan(30);
 }
 await page.evaluate(()=>window.sRunReview.setPhase(.4,'REAR_3_4'));await page.screenshot({path:testInfo.outputPath('contact-v3.png')});expect(errors).toEqual([]);
});

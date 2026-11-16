import {chromium} from 'playwright';import fs from 'node:fs';
const out=process.env.D3C_OUT||'docs/2p5d/evidence/20261117-s-d3c-v2';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage(),result=[];
for(const variant of ['authored-v1','authored-v2']){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder='+variant);await page.waitForFunction(()=>window.sRunReview);
 result.push(await page.evaluate(variant=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview,conditions=[];
  for(const rate of [.5,1,1.5]){const frames=[];for(let i=0;i<=96;i++){s.setRate(rate);s.setPhase(i/96,'SIDE',false);const m=s.motionSample();frames.push({phase:i/96,body:s.bodySample(),limbs:m.contact.limbs.map(l=>({name:l.name,joints:l.joints,angles:l.jointAngles,stage:l.stage,anchor:l.anchor})),bodySkin:s.probe(s.bodyVertexIds)});}conditions.push({rate,frames});}return {variant,asset:s.sample().asset,conditions};
 },variant));
}
const qAngle=(a,b)=>2*Math.acos(Math.min(1,Math.abs(a.reduce((s,x,i)=>s+x*b[i],0))))*180/Math.PI;
const summary=result.map(r=>({variant:r.variant,conditions:r.conditions.map(c=>({rate:c.rate,bones:c.frames[0].body.map((bone,i)=>{const samples=c.frames.map(f=>f.body[i]);return {name:bone.name,angularSpan:Math.max(...samples.map(x=>qAngle(bone.quaternion,x.quaternion))),verticalSpan:Math.max(...samples.map(x=>x.position[1]))-Math.min(...samples.map(x=>x.position[1]))};}),fore:c.frames[0].limbs.slice(0,2).map((l,i)=>({name:l.name,minElbow:Math.min(...c.frames.map(f=>f.limbs[i].angles[0])),maxElbow:Math.max(...c.frames.map(f=>f.limbs[i].angles[0])),shoulderLocalTravel:Math.max(...c.frames.map(f=>f.limbs[i].joints[0][2]-f.phase*4*c.rate/(2.4*Math.sqrt(c.rate))))-Math.min(...c.frames.map(f=>f.limbs[i].joints[0][2]-f.phase*4*c.rate/(2.4*Math.sqrt(c.rate))))}))}))}));
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/articulation-samples.json',JSON.stringify(result));fs.writeFileSync(out+'/articulation-summary.json',JSON.stringify(summary,null,2));await browser.close();

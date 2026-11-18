import {chromium} from 'playwright';import fs from 'node:fs';import {gzipSync} from 'node:zlib';
const out='docs/2p5d/evidence/20261027-s-toe-structure-d1a';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:960,height:640}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
const data=await page.evaluate(()=>{
 const api=window.sRunReview;api.setRate(1);api.setPhase(0,'SIDE');const surfaces=api.footSurfaces,frames=[];
 for(let i=0;i<=240;i++){
  if(i)api.step((1/2.4)/240);
  const state=api.motionSample();frames.push({phase:i/240,distance:state.distance,contact:state.contact,feet:api.footSample().map(({points,...f})=>f)});
 }
 const probes=[];
 for(let foot=0;foot<4;foot++)for(const degrees of [0,5,10,15,20,25,30,35]){
  api.setPhase([.74,.82,.29,.38][foot],'SIDE');const before=api.footSample()[foot],after=api.probeFootRotation(foot,degrees);
  probes.push({foot,degrees,before:{pitch:before.pitchDegrees,minY:before.minY,rear:before.rear,front:before.front},after:{pitch:after.pitchDegrees,minY:after.minY,rear:after.rear,front:after.front}});
 }
 return {surfaces,frames,probes};
});
fs.writeFileSync(`${out}/structure.json`,JSON.stringify(data.surfaces,null,2)+'\n');fs.writeFileSync(`${out}/baseline-cycle.json.gz`,gzipSync(JSON.stringify(data.frames)));fs.writeFileSync(`${out}/terminal-rotation-probes.json`,JSON.stringify(data.probes,null,2)+'\n');
const report=data.surfaces.map((s,i)=>({name:s.name,vertices:s.ids.length,minTerminalWeight:s.minTerminalWeight,rearIds:s.rearIds,frontIds:s.frontIds,sweep:s.sweep,pitchRange:[Math.min(...data.frames.map(f=>f.feet[i].pitchDegrees)),Math.max(...data.frames.map(f=>f.feet[i].pitchDegrees))],stanceRearYRange:[Math.min(...data.frames.filter(f=>['CONTACT','PUSH'].includes(f.contact.limbs[i].stage)).map(f=>f.feet[i].rear[1])),Math.max(...data.frames.filter(f=>['CONTACT','PUSH'].includes(f.contact.limbs[i].stage)).map(f=>f.feet[i].rear[1]))]}));
fs.writeFileSync(`${out}/summary.json`,JSON.stringify({errors,report},null,2)+'\n');
for(const view of ['SIDE','LOW']){await page.evaluate(view=>window.sRunReview.setPhase(.32,view),view);await page.screenshot({path:`${out}/baseline-${view}.png`});}
console.log(JSON.stringify(report.map(({rearIds,frontIds,...s})=>s),null,2));await browser.close();

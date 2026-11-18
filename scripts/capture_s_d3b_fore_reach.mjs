// Direct original-GLB WebGL evidence, no synthetic frames or model replacement.
import {chromium,devices} from 'playwright';
import fs from 'node:fs';
const out='docs/2p5d/evidence/20261029-s-d3b-fore-reach';
fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}});
const observations=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
for(const [label,body] of [['before','push-v3'],['after','push-v5']]){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body='+body);
 await page.waitForFunction(()=>window.sRunReview?.bodySample);
 await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const rate of [.5,1,1.5]){
  for(const view of ['SIDE','REAR_3_4']){
   for(const phase of [.20,.32,.64,.75,.90]){
    const o=await page.evaluate(({rate,view,phase})=>{
      const a=window.sRunReview;
      a.setRate(rate);a.setPhase(phase,view,false);
      a.advance(0);
      const state=a.motionSample(),body=a.bodySample();
      return {rate,view,phase,legs:state.contact.limbs.map(l=>({
       name:l.name,stage:l.stage,reachError:l.reachError,foreVisualReach:l.foreVisualReach,
       toe:l.toe?.mode,foot:l.joints.at(-1),target:l.target,anchor:l.anchor
      })),body:body.filter(b=>['pelvis','spine','chest','neck','head'].includes(b.name)).map(b=>({name:b.name,q:b.quaternion,position:b.position}))};
    },{rate,view,phase});
    observations.push({label,...o});
    await page.screenshot({path:out+'/'+label+'-'+view+'-'+String(rate).replace('.','p')+'x-p'+String(Math.round(phase*100)).padStart(2,'0')+'.png'});
   }
  }
 }
}
fs.writeFileSync(out+'/fore-reach-visual-probes.json',JSON.stringify({source:'actual original S skinned GLB WebGL',observations,pageErrors:errors},null,2)+'\n');
await browser.close();
if(errors.length)throw Error(JSON.stringify(errors));
console.log('D3B_VISUAL_PROBES_COMPLETE',observations.length);

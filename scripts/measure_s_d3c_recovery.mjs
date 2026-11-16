import {chromium} from 'playwright';
import fs from 'node:fs';
const out=process.env.D3C_OUT||'docs/2p5d/evidence/20261117-s-d3c-v3';
const variants=(process.env.D3C_VARIANTS||'authored-v1,authored-v2').split(',');
const phases=[...new Set([...Array.from({length:34},(_,i)=>Number((.14+i*.01).toFixed(3))),.307,.473])].sort((a,b)=>a-b);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}}),rows=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
for(const variant of variants){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder='+variant);await page.waitForFunction(()=>window.sRunReview);
 rows.push(...await page.evaluate(({variant,phases})=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview,rows=[];s.setRate(1);
  for(const view of ['SIDE','REAR_3_4'])for(const phase of phases){s.setPhase(phase,view,false);rows.push({variant,...s.recoveryAudit()});}return rows;
 },{variant,phases}));
}
const dist=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
const summary=variants.map(variant=>{const r=rows.filter(r=>r.variant===variant&&r.view==='SIDE');return {variant,points:r.length,closest:r.reduce((a,b)=>a.full.centroidDistance<b.full.centroidDistance?a:b).phase,minCentroidDistance:Math.min(...r.map(x=>x.full.centroidDistance)),minSurfaceDistance:Math.min(...r.map(x=>x.full.nearestSurfaceDistance)),maxDoubleIkChange:Math.max(...r.flatMap(x=>x.first.fore.map((f,i)=>dist(f.centroid,x.zeroSecond.fore[i].centroid)))),maxForeReachEffect:Math.max(...r.flatMap(x=>x.full.fore.map((f,i)=>dist(f.centroid,x.withoutForeReach.fore[i].centroid)))),minElbows:[0,1].map(i=>Math.min(...r.map(x=>x.full.fore[i].elbowDegrees))),phase307:r.find(x=>x.phase>.306&&x.phase<.308)};});
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/recovery-'+variants.join('-')+'.json',JSON.stringify({phases,errors,rows}));fs.writeFileSync(out+'/recovery-'+variants.join('-')+'-summary.json',JSON.stringify(summary,null,2));
console.log(JSON.stringify(summary.map(({phase307,...s})=>({...s,at307:{gap:phase307.full.centroidDistance,fore:phase307.full.fore.map(f=>({name:f.name,stage:f.contact.stage,elbow:f.elbowDegrees,rootZ:f.rootZ,relativeToChest:f.relativeToChest})),guide:phase307.guide}})),null,2));await browser.close();

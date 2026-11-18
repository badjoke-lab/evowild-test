import {chromium} from 'playwright';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {summarizeContactRun} from '../src/s_sole_metrics.js';
const out=process.argv[2]||'docs/2p5d/evidence/20261026-s-speeds-b3';
fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}}),errors=[],reports=[];page.on('pageerror',e=>errors.push(e.message));
for(const rig of ['hind-v2','contact-v3']){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig='+rig);await page.waitForFunction(()=>window.sRunReview);
 for(const rate of [.5,1,1.5]){
  const trace=await page.evaluate(rate=>window.sRunReview.measureCycle(rate,240),rate);
  fs.writeFileSync(`${out}/${rig}-${rate}-trace.json.gz`,gzipSync(JSON.stringify(trace)));
  const summary=summarizeContactRun(trace);reports.push({rig,rate,...summary});
  const viewStates=[];
  for(const view of ['SIDE','CHASE','LOW','REAR_3_4']){
   // Four consecutive browser poses per view at each actual speed.
   for(let frame=0;frame<4;frame++){
    const state=await page.evaluate(({phase,view})=>window.sRunReview.setPhase(phase,view),{phase:frame/4,view});viewStates.push(state);
    await page.screenshot({path:`${out}/${rig}-${rate}-${view}-${frame}.png`});
   }
  }
  fs.writeFileSync(`${out}/${rig}-${rate}-views.json`,JSON.stringify(viewStates,null,2)+'\n');
  console.log(JSON.stringify({rig,rate,period:summary.duration,stride:summary.distance,feet:summary.feet.map(({phases,...f})=>f)}));
 }
}
// Explicit diagnostic of instantaneous rate switching; do not pretend the
// constant-rate stance guarantee automatically covers transitions.
const transitions=[];
for(const phase of [.2,.7]){
 await page.selectOption('#speed','0.5');await page.evaluate(p=>window.sRunReview.setPhase(p,'REAR_3_4'),phase);
 const before=await page.evaluate(()=>({state:window.sRunReview.sample(),soles:window.sRunReview.soleSample()}));
 await page.selectOption('#speed','1.5');const after=await page.evaluate(()=>{window.sRunReview.advance(0);return {state:window.sRunReview.sample(),soles:window.sRunReview.soleSample()};});
 transitions.push({phase,before,after,maxVertexJump:Math.max(...after.soles.flatMap((s,i)=>s.points.map((p,k)=>Math.hypot(...p.map((x,d)=>x-before.soles[i].points[k][d])))))});
}
fs.writeFileSync(`${out}/speed-transitions.json`,JSON.stringify(transitions,null,2)+'\n');
fs.writeFileSync(`${out}/summary.json`,JSON.stringify({errors,reports},null,2)+'\n');await browser.close();

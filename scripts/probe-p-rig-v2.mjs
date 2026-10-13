import fs from 'node:fs';
import {chromium,devices} from '@playwright/test';
const dir=process.env.P_PROBE_DIR||'work/p-rig-v2';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
try{
 for(const spec of [{name:'isolated',query:'&motionReview=1'},{name:'desktop',query:''},{name:'mobile',query:'',mobile:true}]){
  const context=await browser.newContext({...spec.mobile?devices['Pixel 7']:{viewport:{width:1280,height:720}},deviceScaleFactor:1});
  const page=await context.newPage(),stamp=new Date('2026-10-13T00:00:00Z');
  await page.clock.install({time:stamp});await page.clock.pauseAt(stamp);
  await page.goto(`http://127.0.0.1:4173/evowild-test/race-quality.html?selected=2&pRig=1&pRigReview=1${spec.query}`);
  await page.waitForFunction(()=>document.querySelector('#stage').dataset.pRigStatus==='ready');await page.clock.runFor(4600);
  await page.evaluate(()=>{
   window.__probe=[];let last=-Infinity;
   const collect=()=>{
    const r=window.__pRigReview;
    if(r&&r.time-last>30){last=r.time;window.__probe.push(structuredClone({...r,field:Object.values(window.__pRigField)}));}
    requestAnimationFrame(collect);
   };requestAnimationFrame(collect);
  });
  await page.clock.runFor(6600);
  const samples=await page.evaluate(()=>window.__probe);
  fs.writeFileSync(`${dir}/${spec.name}-probe.json`,JSON.stringify(samples)+'\n');
  await page.screenshot({path:`${dir}/${spec.name}-probe.png`});
  const summary={samples:samples.length,cycles:samples.at(-1).cycle-samples[0].cycle,
   maxBodyOffset:Math.max(...samples.flatMap(s=>s.field.map(r=>r.bodyOffset))),
   maxBodySink:Math.max(...samples.flatMap(s=>s.field.map(r=>r.bodySink))),
   maxLaneLag:Math.max(...samples.flatMap(s=>s.field.map(r=>Math.abs(r.laneLag)))),
   maxReach:Math.max(...samples.flatMap(s=>s.field.flatMap(r=>r.feet.map(f=>f.reachError)))),
   maxBoneError:Math.max(...samples.flatMap(s=>s.field.flatMap(r=>r.feet.map(f=>f.boneLengthError)))),
   flightSamples:samples.filter(s=>s.feet.every(f=>!f.stance)).length};
  console.log(spec.name,JSON.stringify(summary));await context.close();
 }
}finally{await browser.close();}

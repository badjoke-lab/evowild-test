// Capture real race-quality.html rendering at a controlled 60 Hz clock.
// MP4s contain browser screenshots, never blended or interpolated artwork.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { chromium, devices } from '@playwright/test';

const evidence='docs/evidence/p-revision-20261011';
const scratch='work/p-revision/capture';
const base=process.env.P_REVIEW_URL||'http://127.0.0.1:4173/evowild-test/';
const fixedTime=new Date('2026-10-11T00:00:00Z');
const run=(exe,args)=>new Promise((resolve,reject)=>{const p=spawn(exe,args,{stdio:['ignore','ignore','pipe']});let err='';p.stderr.on('data',x=>err+=x);p.on('error',reject);p.on('close',c=>c===0?resolve():reject(new Error(err)));});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const captures=[];
try {
  for(const spec of [
    {name:'isolated-continuous',query:'motionReview=1&selected=2',seconds:6,viewport:{width:1280,height:720}},
    {name:'race-18-desktop',query:'selected=2',seconds:6,viewport:{width:1280,height:720}},
    {name:'race-18-mobile',query:'selected=2',seconds:4,mobile:true,viewport:{width:412,height:839}}
  ]){
    const context=await browser.newContext({...spec.mobile?devices['Pixel 7']:{},viewport:spec.viewport,deviceScaleFactor:1});
    // Chromium requests this missing site icon automatically. It is unrelated
    // to race assets; fulfill only this verified 404, retaining all other errors.
    await context.route('**/favicon.ico',route=>route.fulfill({status:204,body:''}));
    const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    await page.clock.install({time:fixedTime});await page.clock.pauseAt(fixedTime);
    await page.goto(`${base}race-quality.html?${spec.query}`,{waitUntil:'networkidle'});
    await page.waitForFunction(()=>document.querySelector('#stage').dataset.runSheets==='ready');
    await page.clock.runFor(4600);
    const folder=`${scratch}/${spec.name}`;fs.mkdirSync(folder,{recursive:true});
    const samples=[];
    for(let i=0;i<spec.seconds*60;i++){
      const delta=Math.round((i+1)*1000/60)-Math.round(i*1000/60);await page.clock.runFor(delta);
      const data=await page.locator('#stage').evaluate(el=>({...el.dataset}));
      samples.push({ms:Math.round((i+1)*1000/60),frame:Number(data.selectedRunFrame),position:Number(data.pRunPosition),phase:data.selectedRunPhase,distance:Number(data.selectedDistance),speed:Number(data.selectedSpeed),pixelsPerMeter:Number(data.pixelsPerMeter),selectedX:Number(data.selectedX),selectedY:Number(data.selectedY),fieldSize:Number(data.fieldSize),visibleRacers:Number(data.visibleRacers)});
      await page.screenshot({path:`${folder}/${String(i).padStart(4,'0')}.png`});
      if(i===0||i===180)await page.screenshot({path:`${evidence}/${spec.name}${i===0?'':'-later'}.png`});
    }
    assert.equal(samples[0].fieldSize,18);assert.ok(samples.every(s=>s.position>=samples[0].position));
    const cycles=(samples.at(-1).position-samples[0].position)/6;
    assert.ok(cycles>=3,`${spec.name} must show at least 3 full cycles`);assert.deepEqual(errors,[]);
    const out=`${evidence}/${spec.name}.mp4`;
    await run('ffmpeg',['-y','-loglevel','error','-framerate','60','-i',`${folder}/%04d.png`,'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',out]);
    captures.push({name:spec.name,url:`race-quality.html?${spec.query}`,viewport:spec.viewport,seconds:spec.seconds,fps:60,cycles,observedFrames:[...new Set(samples.map(s=>s.frame))].sort((a,b)=>a-b),errors,samples});
    fs.writeFileSync(`${evidence}/${spec.name}-capture.json`,JSON.stringify(captures.at(-1),null,2)+'\n');
    console.log(`${spec.name}: ${cycles.toFixed(2)} cycles, ${samples.length} browser screenshots`);
    await context.close();
  }
  // Exercise pause, restart and a real UI command. Sample at 8 ms so no drawn
  // 60 Hz frame is missed when checking the ordered phase progression.
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage();
  await page.clock.install({time:fixedTime});await page.clock.pauseAt(fixedTime);
  await page.goto(`${base}race-quality.html?motionReview=1&selected=2`,{waitUntil:'networkidle'});
  await page.clock.runFor(33000);
  await page.locator('#agentTargetSelect').selectOption('1');
  await page.locator('[data-agent-command="CONSERVE"]').click({force:true});
  const cadence=[];
  for(let i=0;i<500;i++){await page.clock.runFor(8);cadence.push(await page.locator('#stage').evaluate(el=>({position:Number(el.dataset.pRunPosition),frame:Number(el.dataset.selectedRunFrame),speed:Number(el.dataset.selectedSpeed)})));}
  const deltas=cadence.slice(1).map((s,i)=>s.position-cadence[i].position),jumps=cadence.slice(1).map((s,i)=>(s.frame-cadence[i].frame+12)%12);
  assert.ok(deltas.every(d=>d>=0&&d<=.224));assert.ok(jumps.every(d=>d<=1));
  await page.getByRole('button',{name:'Pause',exact:true}).click({force:true});
  const paused=await page.locator('#stage').getAttribute('data-p-run-position');await page.clock.runFor(1000);
  assert.equal(await page.locator('#stage').getAttribute('data-p-run-position'),paused);
  await page.getByRole('button',{name:'Reset',exact:true}).click({force:true});await page.clock.runFor(16);
  assert.equal(Number(await page.locator('#stage').getAttribute('data-p-run-position')),.87);
  const cadenceAudit={samples:cadence,minDelta:Math.min(...deltas),maxDelta:Math.max(...deltas),largestForwardPhaseStep:Math.max(...jumps),pauseStable:true,resetPosition:.87};
  await context.close();
  await run('ffmpeg',['-y','-loglevel','error','-i',`${evidence}/isolated-continuous.mp4`,'-vf','setpts=2*PTS','-r','60','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',`${evidence}/isolated-half-speed.mp4`]);
  const assetHash=crypto.createHash('sha256').update(fs.readFileSync('public/concept/p-run-sheet.webp')).digest('hex');
  fs.writeFileSync(`${evidence}/video-audit.json`,JSON.stringify({method:'actual browser screenshots, deterministic fixed-step simulation, no interpolation',assetHash,captures,cadenceAudit},null,2)+'\n');
} finally {await browser.close();}

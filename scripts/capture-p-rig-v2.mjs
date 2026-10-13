// Actual browser frames and actual painted foot masks. No video interpolation.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {chromium,devices} from '@playwright/test';
const dir='docs/evidence/p-rig-v2-20261013',scratch='work/p-rig-v2/capture';
const base=process.env.P_REVIEW_URL||'http://127.0.0.1:4173/evowild-test/';
const stamp=new Date('2026-10-13T00:00:00Z');
const run=(cmd,args)=>new Promise((resolve,reject)=>{const p=spawn(cmd,args,{stdio:['ignore','ignore','pipe']});let error='';p.stderr.on('data',x=>error+=x);p.on('error',reject);p.on('close',c=>c?reject(Error(error)):resolve());});
const stats=a=>({n:a.length,mean:a.reduce((x,y)=>x+y,0)/Math.max(1,a.length),max:Math.max(0,...a)});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const results=[];
try{
 for(const spec of [
  {name:'isolated-continuous',rig:true,isolated:true,seconds:6,viewport:{width:1280,height:720}},
  {name:'race-18-desktop',rig:true,seconds:6,viewport:{width:1280,height:720}},
  {name:'race-18-mobile',rig:true,mobile:true,seconds:4,viewport:{width:412,height:839}}
 ]){
  const context=await browser.newContext({...spec.mobile?devices['Pixel 7']:{},viewport:spec.viewport,deviceScaleFactor:1});
  await context.route('**/favicon.ico',r=>r.fulfill({status:204,body:''}));
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.clock.install({time:stamp});await page.clock.pauseAt(stamp);
  const query=`selected=2${spec.isolated?'&motionReview=1':''}${spec.rig?'&pRig=1&pRigReview=1':''}`;
  await page.goto(`${base}race-quality.html?${query}`,{waitUntil:'networkidle'});
  await page.waitForFunction(rig=>document.querySelector('#stage').dataset.runSheets==='ready'&&(!rig||document.querySelector('#stage').dataset.pRigStatus==='ready'),spec.rig);
  const bands=spec.rig?null:await page.evaluate(async()=>{
   const im=new Image();im.src='/evowild-test/concept/p-run-sheet.webp';await im.decode();const c=document.createElement('canvas');c.width=416;c.height=320;const x=c.getContext('2d',{willReadFrequently:true});
   return Array.from({length:12},(_,i)=>{x.clearRect(0,0,416,320);x.drawImage(im,i%4*416,Math.floor(i/4)*320,416,320,0,0,416,320);const p=x.getImageData(0,0,416,320).data,b=[];for(let xx=0;xx<416;xx++){let n=0;for(let y=291;y<296;y++)if(p[(y*416+xx)*4+3]>12)n++;if(n<2)continue;const last=b.at(-1);if(!last||xx-last[1]>7)b.push([xx,xx]);else last[1]=xx;}return b.map(a=>(a[0]+a[1])/2);});
  });
  await page.clock.runFor(4600);const samples=[],frames=[];
  const folder=`${scratch}/${spec.name}`;fs.mkdirSync(folder,{recursive:true});
  for(let i=0;i<spec.seconds*60;i++){
   await page.clock.runFor(Math.round((i+1)*1000/60)-Math.round(i*1000/60));
   const sample=await page.evaluate(({rig,pixels})=>{
    const d=document.querySelector('#stage').dataset;
    const common={frame:Number(d.selectedRunFrame),oldCycle:Number(d.pRunPosition)/6,fieldSize:Number(d.fieldSize),visible:Number(d.visibleRacers),renderer:d.pRenderer,distance:Number(d.selectedDistance),ppm:Number(d.pixelsPerMeter),drawWidth:Number(d.pRenderedDrawWidth)};
    if(!rig)return common;
    const r=window.__pRigReview;
    return {...common,...r,field:Object.values(window.__pRigField),rasters:pixels?r.feet.filter(f=>f.stance).map(f=>({id:f.id,...window.__pRigFootRaster(f.id)})):[]};
   },{rig:spec.rig,pixels:i%2===0});
   frames.push({index:i,cycle:spec.rig?sample.cycle:sample.oldCycle,phase:sample.phase??sample.frame/12,visible:sample.visible,flight:sample.feet?.every(f=>!f.stance)});
   if(i%2===0)samples.push(sample);
   await page.screenshot({path:`${folder}/${String(i).padStart(4,'0')}.png`});
   if(i===0||i===180)await page.screenshot({path:`${dir}/${spec.name}${i===0?'':'-later'}.png`});
  }
  const deltas=[],soleDeltas=[],centroidDeltas=[],laneDeltas=[],allAnchorDrifts=[],episodes=new Map();
  for(let i=1;i<samples.length;i++){
   const n=samples[i],p=samples[i-1];
   if(!spec.rig){
    if(n.frame!==p.frame||![0,1,2,3,9,10,11].includes(n.frame)||!bands[n.frame].length)continue;
    const x=bands[n.frame].at(-1),wx=s=>s.distance+(x-208)*s.drawWidth/416/s.ppm;
    deltas.push(Math.abs(wx(n)-wx(p))*(n.ppm+p.ppm)/2);continue;
   }
   for(const runner of n.field)for(const f of runner.feet){
    const old=p.field.find(r=>r.id===runner.id)?.feet.find(o=>o.id===f.id);
    if(f.stance&&old?.stance&&f.contactId===old.contactId)allAnchorDrifts.push(Math.max(Math.abs(f.worldX-old.worldX)*n.pixelsPerMeter,Math.abs(f.worldLane-old.worldLane)));
   }
   for(const f of n.feet){
    if(!f.stance)continue;
    const r=n.rasters.find(x=>x.id===f.id),worldFromPixel=x=>n.cameraMeters+(x-n.screenAnchor)/n.pixelsPerMeter;
    const key=`${f.id}/${f.contactId}`;if(!episodes.has(key))episodes.set(key,[]);episodes.get(key).push({world:worldFromPixel(r.solePixelX),ppm:n.pixelsPerMeter});
    const old=p.feet.find(o=>o.id===f.id);if(!old.stance||old.contactId!==f.contactId)continue;
    const pr=p.rasters.find(x=>x.id===f.id),oldWorld=x=>p.cameraMeters+(x-p.screenAnchor)/p.pixelsPerMeter,ppm=(n.pixelsPerMeter+p.pixelsPerMeter)/2;
    deltas.push(Math.abs(f.worldX-old.worldX)*ppm);laneDeltas.push(Math.abs(f.worldLane-old.worldLane));
    soleDeltas.push(Math.abs(worldFromPixel(r.solePixelX)-oldWorld(pr.solePixelX))*ppm);
    centroidDeltas.push(Math.abs(worldFromPixel(r.centroidX)-oldWorld(pr.centroidX))*ppm);
   }
  }
  const cycleCount=frames.at(-1).cycle-frames[0].cycle;
  const summary={name:spec.name,url:`race-quality.html?${query}`,viewport:spec.viewport,fps:60,seconds:spec.seconds,cycles:cycleCount,traceIntervalMs:1000/30,traceSamples:samples.length,visibleRacers:[...new Set(frames.map(f=>f.visible))],errors,
   metric:spec.rig?'Persistent foot ID + stance ID; world anchor and actual alpha foot-mask raster':'Legacy rightmost RGBA ground band during the same held frame; no persistent toe identity',
   anchorOrLegacyBandTravelPx:stats(deltas),soleRasterTravelPx:stats(soleDeltas),footRasterCentroidTravelPx:stats(centroidDeltas),laneDrift:stats(laneDeltas),
   observedStanceRasterSpanPx:stats([...episodes.values()].filter(a=>a.length>=3).map(a=>(Math.max(...a.map(v=>v.world))-Math.min(...a.map(v=>v.world)))*a[0].ppm)),
   maxReachError:spec.rig?Math.max(...samples.flatMap(s=>s.field.flatMap(r=>r.feet.map(f=>f.reachError)))):null,
   maxBoneLengthError:spec.rig?Math.max(...samples.flatMap(s=>s.field.flatMap(r=>r.feet.map(f=>f.boneLengthError)))):null,
   allPWorldAnchorDrift:stats(allAnchorDrifts),
   maxBodySink:Math.max(...samples.flatMap(s=>s.field.map(r=>r.bodySink))),
   maxLaneLag:Math.max(...samples.flatMap(s=>s.field.map(r=>Math.abs(r.laneLag)))),
   flightFrames:frames.filter(f=>f.flight).length,
   maxBodyOffset:spec.rig?Math.max(...samples.flatMap(s=>s.field.map(r=>r.bodyOffset))):null,
   pRunners:spec.rig?[...new Set(samples.map(s=>s.field.length))]:null};
  fs.writeFileSync(`${dir}/${spec.name}-trace.json`,JSON.stringify({summary,bands,samples,frames},null,2)+'\n');
  await run('ffmpeg',['-y','-loglevel','error','-framerate','60','-i',`${folder}/%04d.png`,'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',`${dir}/${spec.name}.mp4`]);
  results.push(summary);fs.writeFileSync(`${dir}/run-validation.json`,JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(summary));
  assert.equal(errors.length,0);assert.ok(cycleCount>=3);assert.ok(samples.every(s=>s.fieldSize===18));
  if(spec.rig){assert.ok(summary.maxBodyOffset<12);assert.ok(summary.maxBodySink<20);assert.ok(summary.allPWorldAnchorDrift.max<.000001);assert.ok(summary.flightFrames>0);assert.ok(summary.maxReachError<.001);assert.ok(summary.maxBoneLengthError<.000001);assert.ok(summary.anchorOrLegacyBandTravelPx.max<.000001);assert.ok(summary.soleRasterTravelPx.mean<1);assert.ok(samples.every(s=>s.feet.length===4));}
  if(!spec.isolated)assert.deepEqual(summary.visibleRacers,[18]);
  await context.close();
 }
 await run('ffmpeg',['-y','-loglevel','error','-i',`${dir}/isolated-continuous.mp4`,'-vf','setpts=2*PTS','-r','60','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',`${dir}/layered-half-speed.mp4`]);
 await run('ffmpeg',['-y','-loglevel','error','-i','docs/evidence/p-layered-20261012/layered-isolated.mp4','-i',`${dir}/isolated-continuous.mp4`,'-filter_complex','[0:v]crop=480:310:360:180[a];[1:v]crop=480:310:360:180[b];[a][b]hstack','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',`${dir}/before-after-motion.mp4`]);
}finally{await browser.close();}

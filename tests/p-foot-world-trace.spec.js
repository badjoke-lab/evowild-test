import {test,expect} from '@playwright/test';
import fs from 'node:fs';
const dir='docs/evidence/p-foot-world-trace-20261012';
const modes=['default','distance'];
const contactPhases=new Set([0,1,2,3,9,10,11]);
function nearestBand(bands){return bands.length?bands.at(-1):null}
test('P actual RGBA support-band travel under both live cadence policies',async({page},info)=>{
 test.setTimeout(180000);
 fs.mkdirSync(dir,{recursive:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const stamp=new Date('2026-10-12T00:00:00Z');
 await page.clock.install({time:stamp});await page.clock.pauseAt(stamp);
 await page.goto('/evowild-test/race-quality.html?motionReview=1&selected=2',{waitUntil:'networkidle'});
 const bands=await page.evaluate(async()=>{
  const im=new Image();im.src='/evowild-test/concept/p-run-sheet.webp';await im.decode();
  const c=document.createElement('canvas');c.width=416;c.height=320;
  const ctx=c.getContext('2d',{willReadFrequently:true});
  return Array.from({length:12},(_,i)=>{
   ctx.clearRect(0,0,416,320);
   ctx.drawImage(im,i%4*416,Math.floor(i/4)*320,416,320,0,0,416,320);
   const p=ctx.getImageData(0,0,416,320).data;
   const xs=[];
   for(let x=0;x<416;x++){
    let count=0;
    for(let y=291;y<=295;y++)if(p[(y*416+x)*4+3]>12)count++;
    if(count>=2)xs.push(x);
   }
   const found=[];
   for(const x of xs){
    const last=found.at(-1);
    if(!last||x-last[1]>7)found.push([x,x]);
    else last[1]=x;
   }
   return found.map(([a,b])=>({left:a,right:b,centre:(a+b)/2}));
  });
 });
 expect(bands.length).toBe(12);
 const runs=[];
 for(const mode of modes){
  const suffix=mode==='distance'?'&pStrideClock=distance':'';
  await page.goto('/evowild-test/race-quality.html?motionReview=1&selected=2'+suffix,{waitUntil:'networkidle'});
  const stage=page.locator('#stage');
  await expect(stage).toHaveAttribute('data-run-sheets','ready');
  await page.clock.runFor(4600);
  const samples=[],holds=[];
  for(let k=0;k<200;k++){
   await page.clock.runFor(33);
   const sample=await stage.evaluate(el=>({
    distance:Number(el.dataset.selectedDistance),
    phase:Number(el.dataset.selectedRunFrame),
    phasePosition:Number(el.dataset.pRunPosition),
    pixelsPerMetre:Number(el.dataset.pixelsPerMeter),
    drawWidth:Number(el.dataset.pRenderedDrawWidth),
    shownModel:el.dataset.pCadenceModel
   }));
   if(!Number.isFinite(sample.distance)||!Number.isFinite(sample.drawWidth)||sample.drawWidth<=0)
     throw Error('Missing valid P review-only rendering measurements');
   const support=contactPhases.has(sample.phase)?nearestBand(bands[sample.phase]):null;
   sample.supportX=support?.centre??null;
   sample.supportWorldX=support?sample.distance+(support.centre-208)*sample.drawWidth/416/sample.pixelsPerMetre:null;
   samples.push(sample);
   const previous=samples.at(-2);
   if(previous&&previous.phase===sample.phase&&sample.supportWorldX!==null&&previous.supportWorldX!==null){
     const deltaWorld=sample.supportWorldX-previous.supportWorldX;
     const meanPx=(sample.pixelsPerMetre+previous.pixelsPerMetre)/2;
     holds.push({phase:sample.phase+1,worldTravelMetres:deltaWorld,projectedTravelPx:deltaWorld*meanPx,
      phaseDistance:sample.phasePosition-previous.phasePosition});
   }
  }
  expect(samples.some(x=>x.phase===6)).toBe(true);
  expect(holds.length).toBeGreaterThan(5);
  const abs=holds.map(x=>Math.abs(x.projectedTravelPx)).sort((a,b)=>a-b);
  runs.push({mode,renderPolicy:samples[0].shownModel,sampleCount:samples.length,
   samePoseSupportHolds:holds.length,
   meanAbsProjectedHoldTravelPx:abs.reduce((a,b)=>a+b,0)/abs.length,
   maxAbsProjectedHoldTravelPx:abs.at(-1),
   p90AbsProjectedHoldTravelPx:abs[Math.floor((abs.length-1)*.9)],
   note:'Support-band x measured from actual RGBA ground-row alpha. World coordinate combines root distance and frame band centre. Does not track a persistent anatomical toe across phase changes.',
   samples,holds});
 }
 const summary={source:'live deterministic Playwright game renderer; 12 real RGBA P atlas phases',
  screenPxScale:'actual renderer width and pixels-per-metre',
  methodologicalLimit:'World support-band proxy; not a semantic toe detector, cannot prove zero foot slip at phase boundaries or frame transitions.',
  notes:'Both modes use the same sprite frames and actual world distance. Tests can confirm phase-clock behavior but not fix stance slip.',
  bands,runs,errors};
 fs.writeFileSync(dir+'/foot-world-trace.json',JSON.stringify(summary,null,2)+'\n');
 const graph=await page.evaluate(results=>{
  const c=document.createElement('canvas');c.width=1100;c.height=600;
  const x=c.getContext('2d');x.fillStyle='#eaf0f4';x.fillRect(0,0,1100,600);
  x.fillStyle='#1b2935';x.font='26px sans-serif';
  x.fillText('P ground-band same-pose travel (actual atlas; not toe IDs)',24,44);
  const colors=['#c24f4b','#345db2'];
  for(let k=0;k<results.length;k++){
    const r=results[k],y=160+k*150;
    x.fillStyle='#263a48';x.font='23px sans-serif';x.fillText(r.mode,y>0?34:34,y);
    x.fillStyle=colors[k];x.fillRect(290,y-27,r.meanAbsProjectedHoldTravelPx*35,44);
    x.fillStyle='#263a48';x.fillText(r.meanAbsProjectedHoldTravelPx.toFixed(2)+' px mean',600,y);
    x.font='15px sans-serif';x.fillText(r.samePoseSupportHolds+' same-frame holds; max '+r.maxAbsProjectedHoldTravelPx.toFixed(2)+' px',290,y+55);
  }
  x.fillStyle='#273c48';x.font='16px sans-serif';
  x.fillText('RGBA ground-contact band (rightmost) + actual world root distance; no per-toe identity.',25,535);
  x.fillText('This visualization does not establish reduced slip at phase changes or animation quality.',25,565);
  return c.toDataURL();
 },runs);
 fs.writeFileSync(dir+'/support-band-travel.png',Buffer.from(graph.split(',')[1],'base64'));
 expect(errors).toEqual([]);
 console.log('P_WORLD_SUPPORT_BAND',JSON.stringify(runs.map(({mode,samePoseSupportHolds,meanAbsProjectedHoldTravelPx,p90AbsProjectedHoldTravelPx,maxAbsProjectedHoldTravelPx})=>({mode,samePoseSupportHolds,meanAbsProjectedHoldTravelPx,p90AbsProjectedHoldTravelPx,maxAbsProjectedHoldTravelPx}))));
});

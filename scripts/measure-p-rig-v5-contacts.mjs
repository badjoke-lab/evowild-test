// Paired v4/v5 controllers and real foot painters on the same live race inputs.
// Instrumentation exists only in the capture response, never the shipped app.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium,devices} from '@playwright/test';
const root='docs/evidence/p-rig-v5-20261015';
let source=fs.readFileSync('src/p_layered.js','utf8');
source="import * as reference from '/evowild-test/work/p-rig-v5/before-rig.js';\n"+source
 .replace('export async function loadPLayered(base){','export async function loadPLayered(base){\n  await reference.loadPLayered(base);')
 .replace('export function drawPLayered(ctx,r,view){','function drawCurrent(ctx,r,view){');
source+=`\nexport function drawPLayered(ctx,r,view){
 const old=reference.drawPLayered(null,r,view),current=drawCurrent(ctx,r,view);
 if(current&&r.id!==undefined){window.__pairedPoses??=new Map();window.__pairedPoses.set(r.id,{v4:old,v5:current});}
 return current;
}\n`;
const stats=a=>({n:a.length,mean:a.reduce((x,y)=>x+y,0)/Math.max(1,a.length),max:Math.max(0,...a)});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const results=[],all=[];
try{
 for(const spec of [{name:'isolated-continuous',seconds:6,isolated:true},{name:'race-18-desktop',seconds:6},{name:'race-18-mobile',seconds:4,mobile:true}]){
  const context=await browser.newContext({...spec.mobile?devices['Pixel 7']:{},viewport:spec.mobile?{width:412,height:839}:{width:1280,height:720},deviceScaleFactor:1});
  await context.route('**/favicon.ico',r=>r.fulfill({status:200,contentType:'image/x-icon',body:fs.readFileSync('public/favicon.ico')}));
  await context.route('**/src/p_layered.js*',r=>r.fulfill({status:200,contentType:'application/javascript',body:source}));
  const page=await context.newPage(),stamp=new Date('2026-10-13T00:00:00Z'),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.clock.install({time:stamp});await page.clock.pauseAt(stamp);
  await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html?selected=2&pRig=1&pRigReview=1'+(spec.isolated?'&motionReview=1':''),{waitUntil:'networkidle'});
  await page.waitForFunction(()=>{const d=document.querySelector('#stage').dataset;return d.pRigStatus==='ready'&&d.runSheets==='ready';});
  await page.clock.runFor(4600);
  await page.evaluate(()=>{
   const canvas=Object.assign(document.createElement('canvas'),{width:128,height:128});
   const ctx=canvas.getContext('2d',{willReadFrequently:true});
   const raster=(pose,f)=>{
    const ox=Math.floor(f.screenX)-64,oy=Math.floor(f.screenY)-96;
    ctx.resetTransform();ctx.clearRect(0,0,128,128);ctx.translate(-ox,-oy);pose.paintFoot(ctx,f.id);
    const data=ctx.getImageData(0,0,128,128).data;
    let bottom=-1,left=128,right=-1,ax=0,weight=0;
    for(let k=0;k<data.length/4;k++){
     const a=data[k*4+3]/255;ax+=(k%128+.5)*a;weight+=a;
     if(data[k*4+3]>128){left=Math.min(left,k%128);right=Math.max(right,k%128);bottom=Math.max(bottom,Math.floor(k/128));}
    }
    let sum=0,n=0;
    for(let y=Math.max(0,bottom-1);y<=bottom;y++)for(let x=left;x<=right;x++)if(data[(y*128+x)*4+3]>128){sum+=x+.5;n++;}
    return {soleX:n?sum/n+ox:null,soleY:bottom+.5+oy,centroidX:ax/weight+ox};
   };
   window.__contactFrames=[];
   const collect=()=>{
    const r=window.__pRigReview;
    if(r)window.__contactFrames.push({time:r.time,camera:r.cameraMeters,anchor:r.screenAnchor,ppm:r.pixelsPerMeter,
     runners:[...window.__pairedPoses].map(([id,poses])=>({id,...Object.fromEntries(Object.entries(poses).map(([version,p])=>[version,{
      bodyOffset:p.bodyOffset,bodySink:p.bodySink,renderLane:p.renderLane,laneLag:p.laneLag,flight:p.flight,spine:p.spine,
      feet:p.feet.map(f=>({id:f.id,stance:f.stance,contactId:f.contactId,worldX:f.worldX,worldLane:f.worldLane,
       screenX:f.screenX,screenY:f.screenY,angle:f.angle,boneLengthError:f.boneLengthError,reachError:f.reachError,hip:f.hip,knee:f.knee,ankle:f.ankle,
       raster:f.stance?raster(p,f):null}))
     }]))}))});
    requestAnimationFrame(collect);
   };requestAnimationFrame(collect);
  });
  await page.clock.runFor(spec.seconds*1000);
  const frames=await page.evaluate(()=>window.__contactFrames);
  const comparisons={supportPoseMaxDelta:0,bodyOffsetMaxDelta:0,renderLaneMaxDelta:0,stanceRasterMaxDelta:0,flightMismatch:0};
  for(const row of frames)for(const r of row.runners){
   comparisons.bodyOffsetMaxDelta=Math.max(comparisons.bodyOffsetMaxDelta,Math.abs(r.v4.bodyOffset-r.v5.bodyOffset));
   comparisons.renderLaneMaxDelta=Math.max(comparisons.renderLaneMaxDelta,Math.abs(r.v4.renderLane-r.v5.renderLane));
   if(r.v4.flight!==r.v5.flight)comparisons.flightMismatch++;
   for(const f of r.v5.feet){
    const b=r.v4.feet.find(p=>p.id===f.id);assert.equal(b.stance,f.stance);assert.equal(b.contactId,f.contactId);
    if(!f.stance)continue;
    for(const j of ['hip','knee','ankle'])comparisons.supportPoseMaxDelta=Math.max(comparisons.supportPoseMaxDelta,Math.hypot(f[j].x-b[j].x,f[j].y-b[j].y));
    comparisons.stanceRasterMaxDelta=Math.max(comparisons.stanceRasterMaxDelta,Math.abs(f.raster.soleX-b.raster.soleX),Math.abs(f.raster.centroidX-b.raster.centroidX),Math.abs(f.raster.soleY-b.raster.soleY));
   }
  }
  const versions=[];
  for(const version of ['v4','v5']){
   const soles=[],centroids=[],anchors=[],lanes=[],verticalResiduals=[],byFoot={};
   for(let i=1;i<frames.length;i++)for(const r of frames[i].runners)for(const f of r[version].feet){
    const key=`${r.id}/${f.id}`;byFoot[key]??={soles:[],anchors:[],lanes:[],centroids:[],verticalResiduals:[]};
    const n=frames[i],p=frames[i-1],old=p.runners.find(x=>x.id===r.id)?.[version].feet.find(x=>x.id===f.id);
    if(!f.stance||!old?.stance||f.contactId!==old.contactId)continue;
    const world=(s,x)=>s.camera+(x-s.anchor)/s.ppm,ppm=(n.ppm+p.ppm)/2;
    const sole=Math.abs(world(n,f.raster.soleX)-world(p,old.raster.soleX))*ppm;
    const centroid=Math.abs(world(n,f.raster.centroidX)-world(p,old.raster.centroidX))*ppm;
    const dy=Math.abs((f.raster.soleY-f.screenY)-(old.raster.soleY-old.screenY));
    const dx=Math.abs(f.worldX-old.worldX),dl=Math.abs(f.worldLane-old.worldLane);
    soles.push(sole);centroids.push(centroid);anchors.push(dx);lanes.push(dl);verticalResiduals.push(dy);
    byFoot[key].soles.push(sole);byFoot[key].centroids.push(centroid);byFoot[key].anchors.push(dx);byFoot[key].lanes.push(dl);byFoot[key].verticalResiduals.push(dy);
   }
   const runners=frames.flatMap(f=>f.runners.map(r=>r[version]));
   const summary={version,frames:frames.length,feet:Object.keys(byFoot).length,solePx:stats(soles),soleVerticalResidualDeltaPx:stats(verticalResiduals),centroidPx:stats(centroids),worldAnchorMetres:stats(anchors),worldLaneDrift:stats(lanes),
    maxBodyOffset:Math.max(...runners.map(r=>r.bodyOffset)),maxBodySink:Math.max(...runners.map(r=>r.bodySink)),maxLaneLag:Math.max(...runners.map(r=>Math.abs(r.laneLag))),
    maxBoneError:Math.max(...runners.flatMap(r=>r.feet.map(f=>f.boneLengthError))),maxReachError:Math.max(...runners.flatMap(r=>r.feet.map(f=>f.reachError))),
    byFoot:Object.fromEntries(Object.entries(byFoot).map(([id,values])=>[id,Object.fromEntries(Object.entries(values).map(([key,list])=>[key,stats(list)]))]))};
   assert.equal(summary.worldAnchorMetres.max,0);assert.equal(summary.worldLaneDrift.max,0);
   if(summary.maxBoneError>=1e-8)console.log(JSON.stringify({failure:summary,worst:runners.flatMap(r=>r.feet).sort((a,b)=>b.boneLengthError-a.boneLengthError).slice(0,3)}));
   assert.ok(summary.maxBoneError<1e-8);assert.equal(summary.maxReachError,0);
   if(!spec.isolated)assert.equal(summary.feet,20);
   versions.push(summary);
  }
  assert.equal(errors.length,0);
  assert.equal(comparisons.flightMismatch,0); // Geometry and planned touchdowns intentionally differ; report, do not assert equality.
  const result={name:spec.name,errors,comparisons,versions};results.push(result);all.push({name:spec.name,frames});
  console.log(JSON.stringify({name:spec.name,comparisons,versions:versions.map(({byFoot,...v})=>v)}));
  await context.close();
 }
 fs.writeFileSync(`${root}/all-20-contact-frames.json`,JSON.stringify(all)+'\n');
 fs.writeFileSync(`${root}/all-20-contact-validation.json`,JSON.stringify({method:'Both real controllers receive identical live race inputs; 16 ms rAF. All visible P feet rasterized separately before scene occlusion. Horizontal movement removes camera motion. Vertical residual movement subtracts the projected ground contact Y before differencing. No pixel tracking of the composited scene.',results},null,2)+'\n');
}finally{await browser.close();}

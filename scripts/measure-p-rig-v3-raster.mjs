// Both real foot painters on identical live contact transforms.
// Full race v2/v3 control equivalence is checked separately by audit-p-rig-v3.py.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium,devices} from '@playwright/test';
const root='docs/evidence/p-rig-v3-20261013';
const beforeSource=fs.readFileSync(`${root}/v2-snapshot/p_layered.js`,'utf8')+`
export const paintReferenceFoot=(target,r,f)=>{
 const contact={x:(f.screenX-r.rootX)/r.scale+208,y:(f.screenY-r.rootY)/r.scale+296};
 target.save();target.translate(r.rootX,r.rootY);target.scale(r.scale,r.scale);target.translate(-208,-296);
 foot(target,atlas.parts[f.id.startsWith('fore')?'fore-foot':'hind-foot'],contact,f.angle,f.id.endsWith('far'));target.restore();
};`;
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const all=[];
const stats=a=>({n:a.length,mean:a.reduce((x,y)=>x+y,0)/Math.max(1,a.length),max:Math.max(0,...a)});
try {
 for(const spec of [{name:'isolated-continuous',seconds:6,isolated:true},{name:'race-18-desktop',seconds:6},{name:'race-18-mobile',seconds:4,mobile:true}]){
  const context=await browser.newContext({...spec.mobile?devices['Pixel 7']:{},viewport:spec.mobile?{width:412,height:839}:{width:1280,height:720},deviceScaleFactor:1});
  await context.route('**/favicon.ico',r=>r.fulfill({status:200,contentType:'image/x-icon',body:fs.readFileSync('public/favicon.ico')}));
  const page=await context.newPage(),stamp=new Date('2026-10-13T00:00:00Z'),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.clock.install({time:stamp});await page.clock.pauseAt(stamp);
  await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html?selected=2&pRig=1&pRigReview=1'+(spec.isolated?'&motionReview=1':''),{waitUntil:'networkidle'});
  await page.waitForFunction(()=>{const d=document.querySelector('#stage').dataset;return d.pRigStatus==='ready'&&d.runSheets==='ready'});
  await page.evaluate(async source=>{
   const v2=await import(URL.createObjectURL(new Blob([source],{type:'text/javascript'})));await v2.loadPLayered('/evowild-test/');
   window.__v2FootRaster=(r,f)=>{
    const ox=Math.floor(f.screenX)-64,oy=Math.floor(f.screenY)-96;
    const c=Object.assign(document.createElement('canvas'),{width:128,height:128}),cx=c.getContext('2d',{willReadFrequently:true});
    cx.translate(-ox,-oy);v2.paintReferenceFoot(cx,r,f);
    const data=cx.getImageData(0,0,128,128).data;
    let bottom=-1,left=128,right=-1,ax=0,weight=0;
    for(let k=0;k<data.length/4;k++){
     const alpha=data[k*4+3]/255;ax+=(k%128+.5)*alpha;weight+=alpha;
     if(data[k*4+3]>128){left=Math.min(left,k%128);right=Math.max(right,k%128);bottom=Math.max(bottom,Math.floor(k/128));}
    }
    let sum=0,n=0;
    for(let y=Math.max(0,bottom-1);y<=bottom;y++)for(let x=left;x<=right;x++)if(data[(y*128+x)*4+3]>128){sum+=x+.5;n++;}
    return {solePixelX:n?sum/n+ox:null,centroidX:ax/weight+ox};
   };
  },beforeSource);
  await page.clock.runFor(4600);
  await page.evaluate(()=>{
   window.__rasterFrames=[];
   const collect=()=>{
    const r=window.__pRigReview;
    if(r)window.__rasterFrames.push({time:r.time,cycle:r.cycle,cameraMeters:r.cameraMeters,screenAnchor:r.screenAnchor,pixelsPerMeter:r.pixelsPerMeter,
     feet:r.feet.map(f=>({id:f.id,stance:f.stance,contactId:f.contactId,worldX:f.worldX,worldLane:f.worldLane,ankle:f.ankle,
      v2:f.stance?window.__v2FootRaster(r,f):null,v3:f.stance?window.__pRigFootRaster(f.id):null}))});
    requestAnimationFrame(collect);
   };requestAnimationFrame(collect);
  });
  await page.clock.runFor(spec.seconds*1000);
  const frames=await page.evaluate(()=>window.__rasterFrames),results=[];
  for(const version of ['v2','v3']){
   const soles=[],centroids=[],anchors=[];
   for(let i=1;i<frames.length;i++)for(const f of frames[i].feet){
    const n=frames[i],p=frames[i-1],old=p.feet.find(x=>x.id===f.id);
    if(!f.stance||!old.stance||old.contactId!==f.contactId)continue;
    const world=(r,x)=>r.cameraMeters+(x-r.screenAnchor)/r.pixelsPerMeter,ppm=(p.pixelsPerMeter+n.pixelsPerMeter)/2;
    anchors.push(Math.abs(f.worldX-old.worldX)*ppm);
    soles.push(Math.abs(world(n,f[version].solePixelX)-world(p,old[version].solePixelX))*ppm);
    centroids.push(Math.abs(world(n,f[version].centroidX)-world(p,old[version].centroidX))*ppm);
   }
   const summary={version,name:spec.name,renderFrames:frames.length,intervalMs:16,errors,solePx:stats(soles),centroidPx:stats(centroids),anchorPx:stats(anchors),limitation:'Selected P02; both actual foot painters on identical live v3 contact transforms, before scene occlusion. Lowest-row switching is distinct from support-anchor movement.'};
   assert.equal(errors.length,0);assert.equal(summary.anchorPx.max,0);assert.ok(summary.centroidPx.max<1);
   results.push(summary);console.log(JSON.stringify(summary));
  }
  all.push({name:spec.name,results,frames});await context.close();
 }
 fs.writeFileSync(`${root}/paired-raster-frames.json`,JSON.stringify(all,null,2)+'\n');
 fs.writeFileSync(`${root}/paired-raster-validation.json`,JSON.stringify({identicalLiveContactTransforms:true,results:all.flatMap(r=>r.results)},null,2)+'\n');
}finally{await browser.close()}

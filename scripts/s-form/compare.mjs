import fs from 'node:fs/promises';
import path from 'node:path';
import {launch} from '../race-integration/browser.mjs';
const origin=process.env.FORM_ORIGIN||'http://localhost:4185/evowild-test/';
const folder=process.env.FORM_WORK||'/tmp/evowild-s-form';
await fs.mkdir(folder,{recursive:true});
const views=[['side',0,0],['front',-90,0],['rear',90,0],['top',0,90],['quarter',-45,13]];
const browser=await launch(),records=[];
try{
const old=await browser.newPage({viewport:{width:1200,height:900}});
const errors=[];old.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
await old.goto(origin+'s-form/README.md').catch(()=>{});
await old.evaluate(async()=>{
 const base=new URL('/evowild-test/s-pixel-lab/',location.origin);
 const {RaceRenderer}=await import(new URL('v4.1/race-renderer.js',base).href);
 const [meta,atlas]=await Promise.all(['v3/assets/manifest.json','v2/assets/angles/index.json'].map(p=>fetch(new URL(p,base)).then(r=>r.json())));
 const c=document.createElement('canvas');document.body.replaceChildren(c);c.style.width='1000px';c.style.height='650px';
 const renderer=new RaceRenderer(c,meta,atlas,()=>{});await renderer.surface.load();
 window.sLab={renderer,meta,state:{},manual:()=>{}};
});console.log('old surface ready');
await old.evaluate(async()=>{
 sLab.manual(true);
 await new Promise((resolve,reject)=>{
   const w=new Worker(new URL('s-pixel-lab/v3/sections.js',new URL('/evowild-test/',location.origin)));
   w.onmessage=({data})=>{if(data.error)reject(Error(data.error));else{sLab.renderer.add(data);resolve();}w.terminate();};
   w.onerror=e=>reject(Error(e.message));w.postMessage({count:128,pose:0,meta:sLab.meta});
 });
 const r=sLab.renderer,original=r.drawActors;
 r.drawActors=function(s,frame,use){window.matchedFrame={ext:frame.ext,aim:frame.aim,eye:frame.eye,right:frame.right,up:frame.up};return original.call(this,s,frame,use);};
 r.canvas.style.width='1000px';r.canvas.style.height='650px';
 Object.assign(sLab.state,{mask:true,course:false,number:1,zoom:1,magnification:1,samples:24,layers:128,idle:true,playing:false,spin:false,time:0,heroAA:0});
});console.log('idle stack ready');
const page=await browser.newPage({viewport:{width:1100,height:800}});page.on('pageerror',e=>errors.push(e.message));
await page.goto(origin+'s-form.html');await page.waitForFunction(()=>window.formStudy?.ready);
for(const [key,yaw,tilt] of views){
 let frame;
 for(const method of ['stack','surface']){
   const shot=await old.evaluate(({yaw,tilt,method})=>{
     Object.assign(sLab.state,{yaw,tilt,method});sLab.renderer.draw(sLab.state);return {png:sLab.renderer.canvas.toDataURL().split(',')[1],...matchedFrame};
   },{yaw,tilt,method});
   await fs.writeFile(path.join(folder,'old-'+method+'-'+key+'.png'),Buffer.from(shot.png,'base64'));
   const {png,...info}=shot;frame=info;
 }
 const png=await page.evaluate(({yaw,tilt,frame})=>{
   Object.assign(formStudy.state,{manual:true,idle:true,ground:false,width:1000,height:650,yaw,tilt,extent:frame.ext,target:frame.aim});
   formStudy.renderer.setClearColor(0x000000);formStudy.draw();
   return formStudy.renderer.domElement.toDataURL().split(',')[1];
 },{yaw,tilt,frame});
 await fs.writeFile(path.join(folder,'new-'+key+'.png'),Buffer.from(png,'base64'));
 records.push({view:key,yaw,tilt,width:1000,height:650,model_units_per_metre:200,pixels_per_authoring_unit:650/(frame.ext*2),...frame});
}
if(errors.length)throw Error(errors.join('\n'));
await fs.writeFile('public/s-form/evidence/comparison-camera.json',JSON.stringify(records,null,2)+'\n');
}finally{await browser.close();}

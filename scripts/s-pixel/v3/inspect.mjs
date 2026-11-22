// Render matching black-background frames through both shipped applications.
// Pass V3_QA_CACHE to retain the captures, or V3_QA_VERSIONS=v3 for a repeat.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {openLab,ROOT} from '../browser.mjs';

const cache=process.env.V3_QA_CACHE || await fs.mkdtemp(path.join(os.tmpdir(),'evowild-s03-'));
const viewport={width:1280,height:900};
const width=512,height=320,period=.72;
const views=[
 ['side',0,0],['front',-90,0],['rear',90,0],['top',0,90],['quarter',-45,13]
];
const recipes=[];
function record(id,group,parameters){
 recipes.push({id,group,...parameters});
}
for(const [key,yaw,tilt] of views)record('view-'+key,'views',{yaw,tilt,time:0,idle:true});
for(let pose=0;pose<24;pose++){
 for(const [key,yaw,tilt] of views){
  record('pose-'+pose+'-'+key,'gait',{yaw,tilt,time:(pose+.05)/24*period,pose,angle:key,span:156});
 }
}
for(let i=0;i<180;i++){
 record('turn-'+i,'turn',{yaw:-180+i*2,tilt:12,time:0,idle:true,span:156});
}
for(let i=0;i<=72;i++){
 const u=i/72;
 record('switch-'+i,'switch',{yaw:-40+65*u,tilt:10+3*Math.sin(Math.PI*u),span:60+202*u,
   time:2.16+u*period*2,progress:u});
}
// Camera elevation and azimuth cuts, including a nearly vertical view over a running pose.
for(let i=0;i<12;i++){
 record('cut-'+i,'cut',{yaw:[0,-90,85,-45,28,159][i%6],tilt:[4,0,45,13,89,28][i%6],
   time:(i+.05)*period/24,span:i<6?124:198});
}
await fs.mkdir(cache,{recursive:true});
await fs.writeFile(path.join(cache,'recipes.json'),JSON.stringify(recipes));
for(const version of (process.env.V3_QA_VERSIONS||'v2,v3').split(',')){
 process.env.LAB_URL=(process.env.LAB_ORIGIN||'http://127.0.0.1:4173')+'/s-pixel-lab/'+version+'/';
 const {page,browser,errors}=await openLab(viewport);
 try{
  await page.evaluate(async({width,height})=>{
   const lab=window.sLab;lab.manual(true);await lab.ready();
   if(lab.ensureStack)await lab.ensureStack();
   const c=lab.renderer.canvas;c.style.width=width+'px';c.style.height=height+'px';
   Object.assign(lab.state,{mask:true,course:false,number:1,zoom:1,magnification:1,samples:24,
     idle:false,playing:false,spin:false,layers:128});
   // Same fit as the shared one-runner camera. No post-capture rescaling is used
   // for the pixel metrics. The live renderer's reported width verifies the fit.
   function magnification(span,yaw,tilt){
    if(!span)return 1;
    const a=yaw*Math.PI/180,e=tilt*Math.PI/180;
    const up=10*Math.cos(e)+370*Math.abs(Math.sin(a)*Math.sin(e))+224*Math.abs(Math.cos(e))+65*Math.abs(Math.cos(a)*Math.sin(e));
    const right=370*Math.abs(Math.cos(a))+65*Math.abs(Math.sin(a));
    return span*Math.max(293,420*height/width,up*1.025,right*height/width*1.025)*2/(700*height);
   }
   window.captureAppearance=async(recipe,method)=>{
    const {yaw,tilt,time,idle,span}=recipe;
    Object.assign(lab.state,{heroAA:method==='lod-race'?0:undefined,yaw,tilt,time,idle:!!idle,method:method==='lod-race'?'lod':method,magnification:magnification(span,yaw,tilt)});
    if(lab.state.method==='lod'&&lab.renderer.sprites?.load)await lab.renderer.sprites.load(Math.round(tilt/10));
    lab.draw();
    const gl=lab.renderer.gl;
    if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL readback failed');
    if(span&&Math.abs((lab.renderer.screenSpan||span)-span)>1.0)throw Error('Camera extent mismatch: '+lab.renderer.screenSpan+' vs '+span);
    const info=lab.renderer.mix?{...lab.renderer.mix}:{};
    return {data:c.toDataURL('image/png').split(',')[1],mix:info,span:lab.renderer.screenSpan};
   };
  },{width,height});
  const methods=process.env.V3_QA_METHODS?.split(',') || (version==='v2'?['stack']:['surface','stack','lod']);
  const groups=process.env.V3_QA_GROUPS?.split(',');
  for(const method of methods){
   const id=version+'-'+method;
   const folder=path.join(cache,id);await fs.mkdir(folder,{recursive:true});
   let draws={};
   try{draws=JSON.parse(await fs.readFile(path.join(folder,'draws.json'),'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
   const work=recipes.filter(r=>{
    if(groups&&!groups.includes(r.group))return false;
    if(process.env.V3_QA_ALL==='1')return true;
    if(version==='v2')return r.group!=='switch'&&r.group!=='cut';
    if(method==='stack')return r.group==='views'||r.group==='switch'||r.group==='cut';
    if(method==='lod')return r.group!=='views';
    return true;
   });
   for(const r of work){
    const result=await page.evaluate(([recipe,m])=>captureAppearance(recipe,m),[r,method]);
    await fs.writeFile(path.join(folder,r.id+'.png'),Buffer.from(result.data,'base64'));
    draws[r.id]={mix:result.mix,span:result.span};
   }
   await fs.writeFile(path.join(folder,'draws.json'),JSON.stringify(draws));
   console.log(id,work.length);
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
if(!process.env.V3_QA_VERSIONS||process.env.V3_QA_PLATES==='1'){
 execFileSync('python3',[path.join(ROOT,'scripts/s-pixel/v3/plates.py'),cache],{stdio:'inherit'});
}
if(!process.env.V3_QA_CACHE)await fs.rm(cache,{recursive:true,force:true});

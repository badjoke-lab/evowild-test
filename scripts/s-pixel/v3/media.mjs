// Orbit and detail studies use fixed simulation times. The three race clips
// record the delivered course frames against the actual browser clock.
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn,execFileSync} from 'node:child_process';
import os from 'node:os';
import {once} from 'node:events';
import {openLab,DEMO} from '../browser.mjs';

const version=process.env.FILM_VERSION || 'v3';
if(!['v3','v4'].includes(version))throw Error('Unknown film version');
const dir=path.join(DEMO,version,'evidence');
const timeline={turntable:144,gallop:144,'lod-transition':120,near10:72,mixed50:72,mixed100:72};
const chosen=process.argv.slice(2);
const origin=process.env.LAB_ORIGIN||'http://127.0.0.1:4173';
process.env.LAB_URL=origin+'/s-pixel-lab/'+version+'/';
const {page,browser,errors}=await openLab({width:1280,height:900});
try{
 await page.evaluate(async()=>{
  const lab=window.sLab;
  lab.manual(true);await lab.ready();await lab.ensureStack();
  const {raceState}=await import('../v3/scenarios.js');
  const out=document.createElement('canvas');out.width=880;out.height=480;
  const ctx=out.getContext('2d');
  const canvas=lab.renderer.canvas;
  const titles={turntable:'360°回転',gallop:'四足走行','lod-transition':'距離LOD切替',near10:'近景 10体',mixed50:'混在 50体',mixed100:'混在 100体'};
  function label(txt,x,y,color='#f3f5ed',size=14){
   ctx.fillStyle=color;ctx.font='600 '+size+'px "Noto Sans CJK JP", sans-serif';ctx.fillText(txt,x,y);
  }
  async function view(settings,w,h){
   canvas.style.width=w+'px';canvas.style.height=h+'px';
   Object.assign(lab.state,{number:1,course:false,idle:false,mask:false,spin:false,zoom:1,
     magnification:1,method:'lod',samples:24,layers:128},settings);
   if(settings.method!=='stack'&&lab.renderer.sprites?.load){
    await lab.renderer.sprites.load(Math.round(lab.state.tilt/10));
   }
   lab.draw();
   if(lab.renderer.gl.getError()!==0)throw Error('WebGL error during capture');
   return {...lab.renderer.mix};
  }
  window.filmFrame=async(name,i,n,encode=true)=>{
   const u=i/(n-1);let phase,t,mix,extra;
   ctx.fillStyle='#24362f';ctx.fillRect(0,0,out.width,out.height);
   ctx.textAlign='left';
   if(name==='lod-transition'){
    // The left and right canvases have exactly matching camera, pose and clock.
    const zoom=.2+.85*(1-Math.cos(2*Math.PI*u))/2;
    t=.4+u*2.88;
    const settings={time:t,yaw:-48+76*u,tilt:10+3*Math.sin(Math.PI*u),magnification:zoom};
    await view({...settings,method:'stack'},438,389);ctx.drawImage(canvas,0,33);
    mix=await view({...settings,method:'lod'},438,389);ctx.drawImage(canvas,442,33);
    label('128層スタック',12,22);label('距離LOD',454,22);
    extra='投影幅 '+Math.round(lab.renderer.screenSpan)+' px';
   }else if(name==='turntable'||name==='gallop'){
    const orbit=name==='turntable';
    const quadrant=Math.min(3,Math.floor(u*4));
    t=orbit?u*2.88:(i%36)/36*lab.meta.period;
    const yaw=orbit?-22+360*u:[0,-90,90,-45][quadrant];
    const tilt=orbit?14:[2,3,3,13][quadrant];
    mix=await view({yaw,tilt,time:t,method:'surface'},877,414);
    ctx.drawImage(canvas,1,8);
    extra=(orbit?'方位 '+Math.round(yaw)+'°':['側面','正面','背面','斜め45°'][quadrant]);
   }else{
    const settings=raceState(name,u,877,414,lab.meta);t=settings.time;
    mix=await view(settings,877,414);ctx.drawImage(canvas,1,8);
    extra='方位 '+Math.round(settings.yaw)+'°  /  俯角 '+Math.round(settings.tilt)+'°';
   }
   phase=1+Math.floor(t/lab.meta.period*24+.00001)%24;
   ctx.fillStyle='#e68d5e';ctx.fillRect(0,427,Math.round(out.width*u),3);
   label('S–01   /   '+titles[name],13,454,'#f6f6ef',18);
   ctx.textAlign='right';
   label(extra+'    ・    ポーズ '+String(phase).padStart(2,'0')+' / 24',866,453,'#e0e6dc',13);
   label('近景 '+(mix.near||0)+'　中景 '+(mix.mid||0)+'　切替 '+(mix.transition||0)+'　遠景 '+(mix.sprite||0)+'　画面外 '+(mix.offscreen||0),866,472,'#b7d3bc',12);
   ctx.textAlign='left';return {png:encode?out.toDataURL('image/png').split(',')[1]:null,mix,pose:phase};
  };
  window.recordRace=async name=>{
   // Warm the two banks reached on this camera trajectory. Use the same GPU
   // completion point as the matched timing run. Encoding cost stays visible.
   if(lab.renderer.sprites?.load){
    for(const bank of [1,2])await lab.renderer.sprites.load(bank);
   }
   const stream=out.captureStream(0),track=stream.getVideoTracks()[0];
   const recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp8',videoBitsPerSecond:7000000});
   const chunks=[];recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
   const stopped=new Promise((resolve,reject)=>{recorder.onstop=resolve;recorder.onerror=reject;});
   await filmFrame(name,0,2,false);recorder.start();track.requestFrame();
   const start=performance.now(),time=[],counts=[],poses=[];
   const r=lab.renderer,gl=r.gl,pixel=new Uint8Array(4);
   for(;;){
    await new Promise(requestAnimationFrame);
    const u=Math.min(1,(performance.now()-start)/3000);
    const f=await filmFrame(name,u,2,false);
    gl.readPixels(r.canvas.width>>1,r.canvas.height>>1,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
    track.requestFrame();time.push(performance.now()-start);counts.push(f.mix);poses.push(f.pose);
    if(u>=1)break;
   }
   await new Promise(done=>setTimeout(done,50));recorder.stop();await stopped;track.stop();
   const data=await new Promise(done=>{const reader=new FileReader();reader.onload=()=>done(reader.result.split(',')[1]);
    reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}));});
   return {data,time,counts,poses};
  };
 });
 for(const name of chosen.length?chosen:Object.keys(timeline)){
  const n=timeline[name];if(!n)throw Error('Unknown capture '+name);
  const file=path.join(dir,name+'.mp4');
  let timing={frames:n,playback_hz:24,sampling:'fixed simulation times; not real-time performance'};
  let counts=[],poses=new Set();
  if(['near10','mixed50','mixed100'].includes(name)){
   const recording=await page.evaluate(key=>recordRace(key),name);
   const folder=await fs.mkdtemp(path.join(os.tmpdir(),'evowild-course-'));
   try{
    const original=path.join(folder,'course.webm');await fs.writeFile(original,Buffer.from(recording.data,'base64'));
    execFileSync('ffmpeg',['-loglevel','error','-y','-i',original,'-vf','fps=24','-an','-c:v','libx264',
      '-threads','2','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',file]);
   }finally{await fs.rm(folder,{recursive:true,force:true});}
   counts=recording.counts;poses=new Set(recording.poses);
   const duration=execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',file],{encoding:'utf8'});
   timing={unique_draws:counts.length,display_duration_s:Number(duration),playback_hz:24,
     sampling:'real browser wall clock; MediaRecorder; encoded at 24 Hz with frame holds; recording overhead included',
     presented_ms:recording.time.map(t=>Math.round(t*10)/10)};
  }else{
  const ff=spawn('ffmpeg',['-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate','24','-i','pipe:0',
    '-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',file],{stdio:['pipe','inherit','inherit']});
  const closed=once(ff,'close');
  try{
   for(let i=0;i<n;i++){
    const frame=await page.evaluate(args=>filmFrame(...args),[name,i,n]);counts.push(frame.mix);poses.add(frame.pose);
    if(!ff.stdin.write(Buffer.from(frame.png,'base64')))await once(ff.stdin,'drain');
   }
  }finally{ff.stdin.end();}
  if((await closed)[0])throw Error('Encoding failed: '+name);
  }
  const filePath=path.join(dir,'films.json');
  let info={};try{info=JSON.parse(await fs.readFile(filePath,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
  info[name]={...timing,poses:[...poses].sort((a,b)=>a-b),
    mix_range:Object.fromEntries(['near','mid','transition','sprite','offscreen'].map(k=>[k,
      [Math.min(...counts.map(m=>m[k]||0)),Math.max(...counts.map(m=>m[k]||0))]]))};
  await fs.writeFile(filePath,JSON.stringify(info,null,1));console.log(name,n,info[name].mix_range);
 }
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}

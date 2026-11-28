import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {launch,ready} from '../race-integration/browser.mjs';
const origin=process.env.FORM_ORIGIN||'http://localhost:4185/evowild-test/';
const out='public/s-form/evidence',temp=process.env.FORM_WORK||'/tmp/evowild-s-form';
await fs.mkdir(temp,{recursive:true});
const browser=await launch(),metadata=[];
async function record(page,name,kind,count=1){
 const data=await page.evaluate(async({kind,count})=>{
   const studio=kind!=='race';
   const source=studio?formStudy.renderer.domElement:document.querySelector('#game');
   if(studio){Object.assign(formStudy.state,{manual:true,ground:true,width:960,height:600,extent:null,target:null});}
   const output=document.createElement('canvas');output.width=studio?960:source.width+(source.width%2);
   output.height=(studio?600:source.height)+40;output.height+=output.height%2;
   const ctx=output.getContext('2d'),stream=output.captureStream(0),track=stream.getVideoTracks()[0];
   const rec=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp8',videoBitsPerSecond:6000000});
   const chunks=[],samples=[];rec.ondataavailable=e=>chunks.push(e.data);
   const done=new Promise((resolve,reject)=>{rec.onstop=resolve;rec.onerror=reject});
   const start=performance.now(),duration=kind==='orbit'?12000:10000;
   rec.start();let switched=false;
   await new Promise(resolve=>{
     function frame(now){
       const t=(now-start)/1000,u=Math.min(1,(now-start)/duration);let label;
       if(studio){
         Object.assign(formStudy.state,{idle:kind==='orbit',time:t,yaw:kind==='orbit'?360*u:[0,-90,90,-45][Math.min(3,Math.floor(u*4))],tilt:kind==='orbit'?10:8});
         formStudy.draw();label=kind==='orbit'?'STATIC / 360 DEG / '+Math.round(u*360)+' deg':'GALLOP / phase '+(t/.72*24%24).toFixed(1)+' / 24';
         samples.push({wall_ms:now-start,phase:kind==='orbit'?null:t/.72*24%24,yaw:formStudy.state.yaw});
       }else{
         const s=raceSnapshot();label='RIDGE OVAL / '+count+(count===18?' MIXED':' S')+' / '+s.view.toUpperCase()+' / '+(s.elapsed_ms/1000).toFixed(2)+' s';
         samples.push({wall_ms:now-start,game_ms:s.elapsed_ms,camera:s.view,rank:s.rank,lod:s.pixels.draw?.mix});
         if(!switched&&u>.45){switched=true;document.querySelector('[data-view=follow]').click();}
       }
       ctx.fillStyle='#172b3a';ctx.fillRect(0,0,output.width,output.height);ctx.drawImage(source,0,40);
       ctx.fillStyle='#fff';ctx.font='16px sans-serif';ctx.fillText('S FORM STUDY / '+label,14,26);track.requestFrame();
       if(u<1)requestAnimationFrame(frame);else resolve();
     }requestAnimationFrame(frame);
   });
   rec.stop();await done;track.stop();
   const encoded=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}));});
   return {encoded,samples,width:output.width,height:output.height};
 },{kind,count});
 await fs.writeFile(temp+'/'+name+'.webm',Buffer.from(data.encoded,'base64'));
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',temp+'/'+name+'.webm','-an','-c:v','libx264','-threads','2','-crf','17','-pix_fmt','yuv420p','-fps_mode','vfr','-movflags','+faststart',out+'/'+name+'.mp4']);
 const {encoded,...info}=data;metadata.push({name,kind,count,sampling:'real browser wall clock / MediaRecorder, no generated animation frames',...info});
 console.log(name,data.samples.length);
}
try{
 const p=await browser.newPage({viewport:{width:1200,height:850}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(origin+'s-form.html');await p.waitForFunction(()=>window.formStudy?.ready);
 await record(p,'turntable','orbit');await record(p,'gallop','gallop');await p.close();
 for(const count of [1,18,50]){
   const page=await browser.newPage({viewport:{width:1200,height:760},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
   await page.goto(origin+'?raceTrial=1&sForm=1&verify=1&look=form&field='+(count===18?'mixed':'s')+'&count='+count);
   await ready(page,true);await page.waitForFunction(()=>raceSnapshot().runners[0].speed>=14,null,{timeout:120000});
   await record(page,'ridge-'+count,'race',count);await page.close();
 }
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(out+'/recordings.json',JSON.stringify({renderer:'Chromium SwiftShader',recordings:metadata},null,2)+'\n');
}finally{await browser.close();}

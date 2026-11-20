import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {openLab,DEMO} from '../browser.mjs';
process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/v2/';
const {page,browser,errors}=await openLab({width:1280,height:900}),dir=path.join(DEMO,'v2/evidence');
try{
 await page.evaluate(async()=>{
  sLab.manual(true);await sLab.renderer.sprites.load(1);
  window.movie=(settings,w,h)=>{
    const c=sLab.renderer.canvas;c.style.width=w+'px';c.style.height=h+'px';
    Object.assign(sLab.state,{method:'lod',number:1,magnification:1,mask:false,course:false,spin:false,idle:false},settings);
    sLab.draw();if(sLab.renderer.gl.getError())throw Error('WebGL capture error');return c;
  };
 });
 for(const name of ['turntable','gallop','lod-transition']){
  const fps=24,n=name==='lod-transition'?168:144;
  const ff=spawn('ffmpeg',['-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',path.join(dir,name+'.mp4')],{stdio:['pipe','inherit','inherit']});
  const ended=once(ff,'close');
  for(let i=0;i<n;i++){
   const raw=await page.evaluate(([name,i,n])=>{
    const t=i/24,u=i/(n-1),out=document.createElement('canvas');out.width=864;out.height=480;
    const ctx=out.getContext('2d');ctx.fillStyle='#27362e';ctx.fillRect(0,0,864,480);
    const caption=(txt,x,y,color='#f2f4eb')=>{ctx.font='bold 14px monospace';ctx.fillStyle=color;ctx.fillText(txt,x,y);};
    let title,detail;
    if(name==='lod-transition'){
      // Both windows follow the same 10 subjects through the bend. Matched
      // projection and gait time; inspect full stack against the live LOD decision.
      const params={yaw:-25+24*u,tilt:12,time:2+t,course:true,number:10,magnification:.52+2.88*(.5-.5*Math.cos(2*Math.PI*u))};
      ctx.drawImage(movie({...params,method:'stack'},432,406),0,27,432,406);
      ctx.drawImage(movie(params,432,406),432,27,432,406);
      caption('128 LAYERS',14,19);caption('DISTANCE LOD',446,19);
      const m=sLab.renderer.mix;title='S–01  /  LOD TRANSITION';detail='MESH '+m.near+'   MIX '+m.transition+'   SPRITE '+m.sprite+'   '+params.magnification.toFixed(2)+'x';
    }else{
      const orbit=name==='turntable';
      const yaw=orbit?-22+u*360:(u<.35?-8:u<.66?-90:90);
      const image=movie({yaw,tilt:orbit?14:5,time:t*(orbit?1:.65),method:'lod'},864,433);
      ctx.drawImage(image,0,0);title='S–01  /  '+(orbit?'360° RUN':'GALLOP');
      detail='FRAME '+(1+Math.floor(sLab.state.time/.72*24)%24)+'   YAW '+Math.round(yaw)+'°   128 LAYERS';
    }
    ctx.fillStyle='#f88b55';ctx.fillRect(0,433,864*u,3);caption(title,14,463);ctx.textAlign='right';caption(detail,850,463,'#d0d9cf');
    return out.toDataURL().split(',')[1];
   },[name,i,n]);
   if(!ff.stdin.write(Buffer.from(raw,'base64')))await once(ff.stdin,'drain');
  }
  ff.stdin.end();if((await ended)[0])throw Error('ffmpeg '+name);console.log(name);
 }
 await page.evaluate(()=>{const c=sLab.renderer.canvas;c.style.width='';c.style.height='';Object.assign(sLab.state,{method:'lod',number:100,course:true,idle:false,time:5.8,yaw:23,tilt:12,magnification:1.7});sLab.sync();sLab.draw();});
 await page.screenshot({path:path.join(dir,'crowd.png')});
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}

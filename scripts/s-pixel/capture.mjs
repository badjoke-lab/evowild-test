import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {openLab,DEMO} from './browser.mjs';
const {browser,page,errors}=await openLab({width:1280,height:900});
const out=path.join(DEMO,'evidence');
const image=async (name,base64)=>fs.writeFile(name,Buffer.from(base64.split(',')[1],'base64'));
try{
 await page.evaluate(()=>{sLab.manual(true);});
 // Transparent readback isolates the rendered specimen, including detached pixels.
 await page.evaluate(()=>{
   window.captureFrame=(s,w=720,h=432,alpha=false)=>{
     const c=sLab.renderer.canvas;c.style.width=w+'px';c.style.height=h+'px';
     Object.assign(sLab.state,s,{mask:alpha});sLab.draw();
     if(!alpha)return c.toDataURL();
     const gl=sLab.renderer.gl,bytes=new Uint8Array(c.width*c.height*4);
     gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
     const cv=document.createElement('canvas');cv.width=c.width;cv.height=c.height;
     const ctx=cv.getContext('2d'),im=ctx.createImageData(cv.width,cv.height);
     for(let y=0;y<cv.height;y++)for(let x=0;x<cv.width;x++){
       const i=(y*cv.width+x)*4,j=((cv.height-y-1)*cv.width+x)*4;
       if(bytes[j]||bytes[j+1]||bytes[j+2]){im.data.set(bytes.subarray(j,j+4),i);}
     }
     ctx.putImageData(im,0,0);return cv.toDataURL();
   };
 });
 await page.evaluate(()=>sLab.selectLayers(128));
 for(const [id,, ,yaw,tilt] of await page.evaluate(()=>sLab.views)){
   const d=await page.evaluate(([yaw,tilt])=>captureFrame({yaw,tilt,course:false,idle:true,number:1,zoom:.89},600,330,true),[yaw,tilt]);
   await image(path.join(DEMO,'assets/views',id+'.png'),d);
 }
 // Twelve evenly spaced states plus in-between poses use one common camera and scale.
 for(let f=0;f<24;f++){
   const d=await page.evaluate(f=>captureFrame({time:f*sLab.meta.period/24,idle:false,yaw:-13,tilt:7,zoom:.94},370,218,true),f);
   await image(path.join(out,'pose-'+String(f).padStart(2,'0')+'.png'),d);
 }
 if(process.argv.includes('--stills'))process.exitCode=0;
 else{
  for(const name of ['turntable','gallop','camera']){
   const fps=24,n=name==='gallop'?144:120;
   const ff=spawn('ffmpeg',['-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,name+'.mp4')],{stdio:['pipe','inherit','inherit']});
   const ended=once(ff,'close');
   for(let f=0;f<n;f++){
    const raw=await page.evaluate(([name,f,n,fps])=>{
      const t=f/fps,turn=name==='turntable',run=name==='gallop';
      const yaw=turn?-22+360*f/(n-1):run?-14:-45+160*f/(n-1);
      const tilt=turn?12:run?8:3+85*Math.sin(Math.PI*f/(n-1))**2;
      // The gallop includes a full-size side study, followed by a tracked bend.
      const course=run&&f>=72;
      const anim=!turn;
      const data=captureFrame({yaw,tilt,course,idle:!anim,time:t*(run&&!course?.72:1),number:1,zoom:course?.88:1},760,442);
      const out=document.createElement('canvas');out.width=760;out.height=484;
      const ctx=out.getContext('2d');ctx.drawImage(sLab.renderer.canvas,0,0,760,442);
      ctx.fillStyle='#26332c';ctx.fillRect(0,442,760,42);ctx.fillStyle='#f88a59';ctx.fillRect(0,442,(f+1)/n*760,3);
      ctx.fillStyle='#f5f5ef';ctx.font='bold 15px monospace';ctx.fillText('S–01  /  '+(turn?'TURNTABLE':run?(course?'GALLOP · COURSE':'GALLOP · STUDIO'):'CAMERA STUDY'),15,469);
      ctx.textAlign='right';ctx.font='12px monospace';ctx.fillText('128 LAYERS   YAW '+Math.round(yaw)+'°   ELEV '+Math.round(tilt)+'°',745,469);
      return out.toDataURL();
    },[name,f,n,fps]);
    if(!ff.stdin.write(Buffer.from(raw.split(',')[1],'base64')))await once(ff.stdin,'drain');
   }
   ff.stdin.end();if((await ended)[0])throw Error('ffmpeg '+name);
   console.log(name+' captured');
  }
 }
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}

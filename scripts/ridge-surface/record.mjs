import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {base,evidence,launch,ready} from '../race-integration/browser.mjs';

const browser=await launch(),metadata=[];
const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'ridge-video-'));
try{
  for(const count of [50,100]){
    const page=await browser.newPage({viewport:{width:1200,height:760},deviceScaleFactor:1});
  if(process.env.RIDGE_ACTORS)await page.route('**/race-integration/actors.js',r=>r.fulfill({path:process.env.RIDGE_ACTORS,contentType:'text/javascript'}));
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    try{
      await page.goto(base+'?raceTrial=1&verify=1&field=s&count='+count);
      await ready(page,true);
      await page.waitForFunction(()=>{const s=raceSnapshot();return s.runners[0].speed>14&&s.pixels.draw&&!s.pixels.draw.atlasPending;},null,{timeout:120000});
      if(count===50)await page.screenshot({path:path.join(evidence,'race-controls.jpg'),type:'jpeg',quality:85});
      const rec=await page.evaluate(async candidate=>{
        const game=document.querySelector('#game'), out=document.createElement('canvas');
        out.width=game.width+(game.width%2);out.height=game.height+40+(game.height%2);
        const ctx=out.getContext('2d'),stream=out.captureStream(0),track=stream.getVideoTracks()[0];
        const recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp8',videoBitsPerSecond:3800000});
        const chunks=[],samples=[];recorder.ondataavailable=e=>chunks.push(e.data);
        const done=new Promise((ok,bad)=>{recorder.onstop=ok;recorder.onerror=bad;});
        const start=performance.now();let changed=false;
        recorder.start();
        await new Promise(resolve=>{
          function capture(now){
            const s=raceSnapshot();
            ctx.fillStyle='#14262c';ctx.fillRect(0,0,out.width,out.height);ctx.drawImage(game,0,40);
            ctx.fillStyle='#fff';ctx.font='17px sans-serif';
            ctx.fillText('Ridge Oval    '+s.runners.length+' S    /    '+candidate+'    /    '+s.view.toUpperCase()+
              '    /    '+document.querySelector('#clock').textContent+'    /    #'+s.selected+'   '+s.rank+' of '+s.runners.length,12,26);
            track.requestFrame();
            samples.push({wall_ms:now-start,game_ms:s.elapsed_ms,view:s.view,rank:s.rank,lod:s.pixels.draw?.mix});
            if(!changed&&now-start>3600){changed=true;document.querySelector('[data-view="follow"]').click();}
            if(now-start<7800)requestAnimationFrame(capture);else resolve();
          }
          requestAnimationFrame(capture);
        });
        recorder.stop();await done;track.stop();
        const blob=new Blob(chunks,{type:'video/webm'});
        const encoded=await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(blob);});
        return {encoded,samples,width:out.width,height:out.height};
      },process.env.RIDGE_ACTORS?'BOTH TRIAL':'BASE 2606922');
      if(errors.length||rec.samples.length<12||!rec.samples.some(s=>s.view==='follow'))throw Error('Invalid footage: '+errors);
      const input=path.join(temporary,count+'.webm'),output=path.join(evidence,'race-'+count+'.mp4');
      await fs.writeFile(input,Buffer.from(rec.encoded,'base64'));
      execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',input,'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-fps_mode','vfr','-movflags','+faststart',output]);
      metadata.push({count,renderer:'Chromium SwiftShader',width:rec.width,height:rec.height,samples:rec.samples});
      console.log(count,rec.samples.length,rec.samples.at(-1).wall_ms);
    }finally{await page.close();}
  }
  await fs.writeFile(path.join(evidence,'recordings.json'),JSON.stringify(metadata,null,1)+'\n');
}finally{await browser.close();await fs.rm(temporary,{recursive:true,force:true});}

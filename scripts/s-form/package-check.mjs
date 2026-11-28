import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {launch,ready} from '../race-integration/browser.mjs';
const origin=process.env.PACKAGE_ORIGIN||'http://localhost:4187/';
const browser=await launch(),page=await browser.newPage({viewport:{width:1200,height:850}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/favicon.ico'))errors.push(r.status()+' '+r.url())});
try{
 await page.goto(origin);await page.waitForURL('**/s-form/');
 assert.equal(await page.locator('video').count(),5);
 const movies=await page.evaluate(async()=>{
   const rows=[];
   for(const v of document.querySelectorAll('video')){
     v.muted=true;await v.play();await new Promise(r=>setTimeout(r,250));v.pause();
     rows.push({source:v.getAttribute('src'),duration:v.duration,time:v.currentTime,width:v.videoWidth,height:v.videoHeight,error:v.error?.message||null});
   }return rows;
 });
 for(const v of movies){assert.ok(v.duration>5&&v.time>0&&v.width>0);assert.equal(v.error,null);}
 await page.goto(origin+'evowild-test/s-form.html');await page.waitForFunction(()=>window.formStudy?.ready);
 await page.selectOption('#motion','run');await page.waitForTimeout(300);
 assert.equal(await page.evaluate(()=>formStudy.mesh.morphTargetInfluences.filter(v=>v>0).length),2);
 await page.goto(origin+'evowild-test/?raceTrial=1&sForm=1&verify=1&look=form&count=1&field=s');await ready(page,true);
 await page.waitForFunction(()=>raceSnapshot().pixels.draw?.form==='anatomical-study-20261128');
 const modes=[];
 for(const mode of ['pixel','form']){
   await page.selectOption('#trial-mode',mode);await ready(page,true);
   await page.waitForTimeout(300);modes.push(await page.evaluate(()=>({mode:raceSnapshot().pixels.mode,error:raceSnapshot().pixels.error,count:raceSnapshot().runners.length})));
 }
 assert.deepEqual(errors,[]);
 await fs.writeFile('public/s-form/evidence/package-check.json',JSON.stringify({movies,modes,errors},null,2)+'\n');
}finally{await browser.close();}

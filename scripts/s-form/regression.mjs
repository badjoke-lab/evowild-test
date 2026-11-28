import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {launch,fixedClock,ready} from '../race-integration/browser.mjs';
const origin=process.env.FORM_ORIGIN||'http://localhost:4185/evowild-test/';
const out='public/s-form/evidence';
const sha=s=>createHash('sha256').update(s).digest('hex');
const original=execFileSync('git',['show','a93fa4b65ea398d4e8ec0560c600f0d50abe1e72:src/main.js']);
assert.equal(sha(original),sha(await fs.readFile('src/main.js')));
const results={main_js_sha256:sha(original),renderer:'Chromium / SwiftShader',cases:[],mobile:[]};
const browser=await launch();
async function run(count,field,mode,mobile=false){
 const page=await browser.newPage(mobile?{viewport:{width:390,height:844},deviceScaleFactor:2.625,isMobile:true,hasTouch:true}:{viewport:{width:1100,height:745},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.setDefaultTimeout(120000);
 await page.addInitScript(fixedClock);
 const tick=n=>page.evaluate(n=>tickRace(n),n);
 const click=sel=>page.locator(sel).dispatchEvent('click');
 try{
 await page.goto(origin+'?raceTrial=1&sForm=1&verify=1&field='+field+'&count='+count+'&look='+mode);
 await ready(page,mode!=='classic');
 const rows=[];
 async function checkpoint(label,shot=false){
   const s=await page.evaluate(()=>{const {pixels,...s}=raceSnapshot();s.runners=s.runners.map(({visible,...r})=>r);return {state:s,pixels,gl:document.querySelector('#game').getContext('webgl2').getError()}});
   assert.equal(s.gl,0);assert.equal(s.pixels.error,null);assert.equal(s.state.runners.length,count);
   if(shot){await page.screenshot({path:out+'/'+(mobile?'phone':'pc')+'-'+count+'-'+mode+'-'+label+'.png'});}
   rows.push({label,state_sha256:sha(JSON.stringify(s.state)),elapsed_ms:s.state.elapsed_ms,rank:s.state.rank,draw:s.pixels.draw?.mix});
 }
 await tick(60);await checkpoint('race',true);
 await click('[data-view=follow]');await tick(50);await checkpoint('follow',true);
 await click('#pause');await tick(2);await checkpoint('pause');
 const prior=await page.evaluate(()=>{const {pixels,...s}=raceSnapshot();s.runners=s.runners.map(({visible,...r})=>r);return s});
 for(const look of ['pixel','form',mode]){
   await page.selectOption('#trial-mode',look,{force:true});await ready(page,true);
   const after=await page.evaluate(()=>{const {pixels,...s}=raceSnapshot();s.runners=s.runners.map(({visible,...r})=>r);return s});
   assert.deepEqual(after,prior,'changing appearance must not mutate simulation');
 }
 await checkpoint('switch-paused');
 await click('#pause');await click('[data-view=tactical]');await tick(10);await checkpoint('tactical');
 await click('[data-view=lab]');await tick(3);await checkpoint('morph');
 await click('[data-view=race]');await click('#reset');await checkpoint('reset');
 assert.deepEqual(errors,[]);return rows;
 }finally{await page.close();}
}
try{
 for(const [n,field] of [[1,'s'],[18,'mixed'],[50,'s']]){
   const old=await run(n,field,'pixel'),form=await run(n,field,'form');
   for(let i=0;i<old.length;i++)assert.equal(old[i].state_sha256,form[i].state_sha256);
   results.cases.push({count:n,field,matching_checkpoints:old.length,old,form});console.log(n,'PC passed');
   await fs.writeFile(out+'/regression.json',JSON.stringify(results,null,2)+'\n');
 }
 for(const [n,field] of [[1,'s'],[18,'mixed'],[50,'s']]){
   results.mobile.push({count:n,field,checkpoints:await run(n,field,'form',true)});console.log(n,'mobile-width passed');
 }
 await fs.writeFile(out+'/regression.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}

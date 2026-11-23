import {chromium} from 'playwright';
import {raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';
import {DEMO} from '../browser.mjs';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
const url=process.env.QA_URL||'http://127.0.0.1:4173/s-pixel-lab/v4.1/';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
 args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[];
try{
 for(const mobile of [false,true]){
  const viewport=mobile?{width:390,height:844}:{width:1280,height:900};
  const ctx=await browser.newContext({viewport,deviceScaleFactor:mobile?2.625:1,isMobile:mobile,hasTouch:mobile});
  const page=await ctx.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
  page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
  await page.goto(url);await page.waitForFunction(()=>!!window.sLab);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  // Follow the real comparison nav instead of injecting a version at runtime.
  if(!mobile){await page.locator('#old').click();await page.waitForFunction(()=>!!window.sLab);}
  const version=mobile?'v4.1':'v4',profile=mobile?'mobile':'desktop';
  assert.equal(await page.locator('#profile').inputValue(),profile);
  await page.locator('button[value="mixed50"]').click();await page.waitForFunction(()=>document.querySelector('#actors').textContent==='50');
  await page.locator('#play').click();await page.locator('#play').click();
  await page.waitForFunction(()=>parseFloat(document.querySelector('#p95').textContent)>0);
  const meta=await page.evaluate(()=>({stride:sLab.meta.stride,period:sLab.meta.period}));
  if(process.env.QA_OFFLINE)await ctx.setOffline(true);
  await page.locator('#device').fill('SwiftShader UI test');
  await page.locator('#run').click();
  await page.waitForFunction(()=>!document.querySelector('#save').disabled,null,{timeout:120000});
  const downloading=page.waitForEvent('download');await page.locator('#save').click();
  const file=await downloading,result=JSON.parse(await fs.readFile(await file.path(),'utf8'));
  assert.equal(result.version,version);assert.equal(result.profile,profile);assert.equal(result.antialias,false);assert.equal(result.device_label,'SwiftShader UI test');
  const {width,height}=result.raster;assert.deepEqual([width,height],mobile?[352,335]:[877,414]);
  assert.equal(result.rows.length,2);
  for(const [j,key] of ['mixed50','mixed100'].entries()){
   const r=result.rows[j];assert.equal(r.scenario,key);assert.equal(r.frames,48);assert.equal(r.samples.length,48);
   r.samples.forEach((s,i)=>{
    const expected=raceState(key,i/48,width,height,meta);
    for(const k of ['time','yaw','tilt','magnification'])assert.ok(Math.abs(s[k]-expected[k])<1e-8);
    assert.equal(s.drawn+s.mix.offscreen,expected.number);
    assert.ok(s.interval_ms>0&&s.submit_ms>=0&&s.sync_ms>=s.submit_ms);
   });
   const dt=r.samples.map(s=>s.interval_ms);assert.equal(r.p95_ms,[...dt].sort((a,b)=>a-b)[45]);
   assert.ok(Math.abs(r.fps-48000/dt.reduce((a,b)=>a+b,0))<1e-8);
  }
  const raster=await page.evaluate(()=>[sLab.renderer.canvas.width,sLab.renderer.canvas.height]);assert.deepEqual(raster,[width,height]);
  await page.locator('#run').click();
  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));delete document.hidden;});
  await page.waitForFunction(()=>!document.querySelector('#run').disabled);
  assert.equal(await page.locator('#save').isDisabled(),true);
  assert.deepEqual(errors,[]);
  checks.push({profile,version,dpr:result.dpr,raster,renderer:result.renderer,frames:96,exported:true,hidden_tab_abort:true,errors});
  await ctx.close();
 }
}finally{await browser.close();}
const name=process.env.QA_OFFLINE?'portable-check.json':'device-check.json';
await fs.writeFile(path.join(DEMO,'v4.1/evidence',name),JSON.stringify(checks,null,1)+'\n');

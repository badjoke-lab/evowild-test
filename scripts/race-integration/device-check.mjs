// Real RAF and real JSON downloads. The software/emulated device labels are explicit.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {base,evidence,launch} from './browser.mjs';

const browser=await launch(),files=[],results=[],checks=[];
const out=path.join(evidence,'measurements');
await fs.mkdir(out,{recursive:true});
async function download(page,button,name){
  const waiting=page.waitForEvent('download');
  await button.click();const file=await waiting;
  const data=await fs.readFile(await file.path());
  const dst=path.join(out,name+'.json');
  await fs.writeFile(dst,data);files.push(dst);
  return JSON.parse(data);
}
try{
  const ctx=await browser.newContext({viewport:{width:1100,height:745},deviceScaleFactor:1});
  const page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);
  assert.equal(await page.locator('#race-trial').isHidden(),true);
  await page.locator('#trial-entry').click();
  await page.locator('#trial-count').selectOption('50');
  await page.locator('#trial-field').selectOption('s');
  await page.locator('#trial-apply').click();
  await page.waitForURL(/count=50/);
  for(const count of [50,100]){
    if(count===100){
      await page.locator('#trial-count').selectOption('100');await page.locator('#trial-apply').click();await page.waitForURL(/count=100/);
    }
    await page.getByText('実機計測',{exact:true}).click();
    for(const look of count===50?['classic','pixel']:['pixel','classic']){
      await page.selectOption('#trial-mode',look);
      await page.waitForFunction(m=>document.getElementById('race-trial').dataset.renderer===m,look);
      await page.locator('#trial-device').fill('Chromium / SwiftShader (software)');
      await page.locator('#trial-measure').click();
      await page.waitForFunction(()=>!document.getElementById('trial-save').disabled,null,{timeout:150000});
      const data=await download(page,page.locator('#trial-save'),'desktop-'+count+'-'+look);
      assert.equal(data.samples.length,96);assert.equal(data.count,count);assert.equal(data.s_count,count);
      const dt=data.samples.map(s=>s.interval_ms);assert.ok(Math.abs(data.fps-96000/dt.reduce((a,b)=>a+b))<1e-9);
      assert.equal(data.p95_ms,[...dt].sort((a,b)=>a-b)[91]);
      if(look==='pixel')for(const s of data.samples){
        assert.ok(s.lod);assert.equal(Object.values(s.lod).reduce((a,b)=>a+b),count);assert.equal(s.atlas_errors.length,0);
      }
      results.push({count,mode:look,fps:data.fps,p95_ms:data.p95_ms,raster:data.raster,
        streaming:data.samples.filter(s=>s.streaming).length,
        camera:data.samples.map(({camera_position,camera_quaternion,distance,rank,lane})=>[camera_position,camera_quaternion,distance,rank,lane])});
      console.log(count,look,data.fps,data.p95_ms);
    }
    const [a,b]=results.slice(-2);
    assert.deepEqual(a.camera,b.camera);assert.deepEqual(a.raster,b.raster);
    delete a.camera;delete b.camera;
  }
  await page.locator('#trial-measure').click();await page.locator('#pause').click();
  assert.equal(await page.locator('#trial-save').isDisabled(),true);assert.equal(await page.locator('#trial-measure').isEnabled(),true);
  assert.deepEqual(errors,[]);checks.push('normal game entry, field restart, native cameras, pause cancels incomplete export');
  await ctx.close();
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2.625,isMobile:true,hasTouch:true});
  const phone=await mobile.newPage();phone.on('pageerror',e=>errors.push(e.message));
  await phone.goto(base+'?raceTrial=1&count=10&field=mixed');await phone.waitForFunction(()=>document.getElementById('race-trial').dataset.renderer==='pixel');
  for(const v of ['follow','tactical','race'])await phone.locator('[data-view="'+v+'"]').click();
  assert.ok(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await phone.getByText('実機計測',{exact:true}).click();
  await phone.locator('#trial-device').fill('Mobile viewport / SwiftShader (emulated)');
  await phone.locator('#trial-measure').click();await phone.waitForFunction(()=>!document.getElementById('trial-save').disabled,null,{timeout:150000});
  const m=await download(phone,phone.locator('#trial-save'),'emulated-10-mixed');
  assert.equal(m.mobile,true);assert.equal(m.antialias,false);assert.equal(m.samples.length,96);
  await phone.locator('a[href="./s-pixel-lab/v4.1/index.html"]').click();
  await phone.waitForFunction(()=>!!window.sLab);
  await phone.locator('#device').fill('Mobile viewport / SwiftShader (emulated)');
  await phone.locator('#run').click();await phone.waitForFunction(()=>!document.getElementById('save').disabled,null,{timeout:120000});
  const legacy=await download(phone,phone.locator('#save'),'standalone-emulated');
  assert.equal(legacy.schema_version,1);assert.deepEqual(legacy.rows.map(r=>r.frames),[48,48]);
  await phone.goto(base+'race-integration/compare.html');
  await phone.locator('#files').setInputFiles(files);
  await phone.waitForFunction(()=>document.querySelectorAll('tbody tr').length===7);
  assert.equal(await phone.locator('table').count(),5);
  assert.equal(await phone.locator('#errors').innerText(),'');
  await phone.locator('#files').setInputFiles(files[0]);assert.equal(await phone.locator('tbody tr').count(),7);
  await phone.locator('#files').setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{}')});
  await phone.waitForFunction(()=>document.getElementById('errors').textContent.includes('broken.json'));
  await phone.locator('#clear').click();assert.equal(await phone.locator('table').count(),0);
  assert.deepEqual(errors,[]);checks.push('mobile touch cameras and export, standalone v4.1 export, compare groups, duplicate and invalid import');
  await mobile.close();
  await fs.writeFile(path.join(evidence,'device-check.json'),JSON.stringify({software:true,checks,results},null,2)+'\n');
}finally{await browser.close();}

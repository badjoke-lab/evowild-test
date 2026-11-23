// Exercise the distributed ZIP after extraction on a fresh server.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {launch} from '../race-integration/browser.mjs';
const [base,work,output]=process.argv.slice(2);
const browser=await launch(), errors=[];
try{
  const page=await browser.newPage({viewport:{width:1100,height:745}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))errors.push(r.status()+' '+r.url());});
  await page.goto(base+'ridge-performance/');
  for(const img of await page.locator('img').all())await img.evaluate(async i=>{i.loading='eager';await i.decode();});
  const movies=await page.locator('video').evaluateAll(videos=>Promise.all(videos.map(async video=>{
    if(!video.readyState)await new Promise((ok,bad)=>{video.onloadedmetadata=ok;video.onerror=bad;});
    return {width:video.videoWidth,height:video.videoHeight,seconds:video.duration};
  })));
  assert.equal(movies.length,2);assert.ok(movies.every(v=>v.seconds>=6&&v.width>500));
  await page.getByRole('link',{name:'S型100体',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#race-trial')?.dataset.renderer==='pixel');
  await page.selectOption('#trial-mode','classic');await page.locator('[data-view="follow"]').click();
  await page.selectOption('#trial-mode','pixel');
  await page.waitForFunction(()=>document.querySelector('#race-trial').dataset.renderer==='pixel');
  await page.goto(base+'race-integration/compare.html');
  await page.locator('#files').setInputFiles(['before','after'].map(v=>path.join(work,'accept-'+v,'pc-100-pixel-race.json')));
  await page.waitForFunction(()=>document.querySelectorAll('tbody tr').length===2);
  const rows=await page.locator('tbody tr').allTextContents();
  assert.equal(await page.locator('table').count(),1);assert.ok(rows.some(r=>r.includes('初回統合'))&&rows.some(r=>r.includes('ridge-surface-ground-1')));
  assert.equal(await page.locator('#errors').innerText(),'');assert.deepEqual(errors,[]);
  const report={movies,display_switch:true,imported_builds:rows,errors};
  await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');console.log('ZIP playback, race switch and matched JSON import passed.');
}finally{await browser.close();}

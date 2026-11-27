import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {launch,ready} from '../race-integration/browser.mjs';
const [origin,output]=process.argv.slice(2),browser=await launch(),result=[];
try{
 for(const mode of ['base','group','color','both']){
  const page=await browser.newPage({viewport:{width:1100,height:745}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto(origin+'/'+mode+'/evowild-test/?raceTrial=1&verify=1&field=s&count=50');
  await ready(page,true);
  await page.waitForFunction(()=>raceSnapshot().pixels.draw);
  const snapshot=await page.evaluate(()=>({draw:raceSnapshot().pixels.draw.mix,stats:window.surfaceTrialStats??null}));
  assert.equal(snapshot.stats?.mode??'base',mode);
  for(const view of ['follow','tactical','lab','race'])await page.locator('[data-view="'+view+'"]').click();
  await page.selectOption('#trial-mode','classic');
  await page.waitForFunction(()=>document.querySelector('#race-trial').dataset.renderer==='classic');
  await page.selectOption('#trial-mode','pixel');
  await page.waitForFunction(()=>document.querySelector('#race-trial').dataset.renderer==='pixel');
  assert.deepEqual(errors,[]);result.push({mode,...snapshot,errors});
  await page.close();
 }
 const page=await browser.newPage();
 await page.goto(origin+'/report/');
 for(const im of await page.locator('img').all())await im.evaluate(async i=>{i.loading='eager';await i.decode();});
 const movies=await page.locator('video').evaluateAll(v=>Promise.all(v.map(async x=>{
  if(!x.readyState)await new Promise((ok,bad)=>{x.onloadedmetadata=ok;x.onerror=bad;});
  return {width:x.videoWidth,height:x.videoHeight,duration:x.duration};
 })));
 assert.equal(movies.length,4);assert.ok(movies.every(v=>v.duration>=5));
 await fs.writeFile(output,JSON.stringify({cases:result,movies},null,2)+'\n');
}finally{await browser.close();}

// Exercise the unpacked static distribution, including a failed first asset
// request and a retry. Only the loopback demo is allowed to serve dependencies.
import assert from 'node:assert/strict';
import path from 'node:path';
import {launch,evidence} from './browser.mjs';
const url=new URL(process.env.PACKAGE_URL||'http://127.0.0.1:4181/');
const browser=await launch();
try{
  const page=await browser.newPage({viewport:{width:1100,height:745}});
  const errors=[],external=[];let failOnce=true;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>{
    const u=new URL(route.request().url());
    if(u.origin!==url.origin){external.push(u.origin);return route.abort();}
    if(failOnce&&u.pathname.endsWith('/v4.1/assets/geometry.gz')){
      failOnce=false;return route.fulfill({status:503,body:'test'});
    }
    return route.continue();
  });
  await page.goto(url.href);
  await page.waitForFunction(()=>document.querySelector('#trial-note')?.textContent.includes('503'));
  assert.equal(await page.locator('#trial-mode').inputValue(),'classic');
  await page.selectOption('#trial-mode','pixel');
  await page.waitForFunction(()=>document.querySelector('#race-trial').dataset.renderer==='pixel');
  assert.equal(await page.locator('#race-trial h2').innerText(),'S型レース試験');
  const fits=await page.evaluate(()=>document.querySelector('#stage').getBoundingClientRect().right<=document.querySelector('.sidebar').getBoundingClientRect().left);
  assert.ok(fits);
  await page.goto(new URL('evowild-test/race-integration/review.html',url).href);
  const videos=await page.evaluate(async()=>{
    const values=[];
    for(const v of document.querySelectorAll('video')){
      if(!v.readyState)await new Promise((ok,bad)=>{v.onloadedmetadata=ok;v.onerror=bad;});
      values.push({width:v.videoWidth,height:v.videoHeight,duration:v.duration});
    }
    for(const im of document.images){im.loading='eager';await im.decode();}
    return values;
  });
  assert.equal(videos.length,2);assert.ok(videos.every(v=>v.duration>2));
  await page.locator('a[href="compare.html"]').click();
  await page.locator('#files').setInputFiles(['desktop-50-classic','desktop-50-pixel','standalone-emulated'].map(n=>path.join(evidence,'measurements',n+'.json')));
  await page.waitForFunction(()=>document.querySelectorAll('tbody tr').length===4);
  assert.equal(await page.locator('table').count(),3);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log(JSON.stringify({asset_failure:'retained classic; retry restored v4.1',controls_fit:fits,
    videos,imported_rows:4,external_requests:external,page_errors:errors}));
}finally{await browser.close();}

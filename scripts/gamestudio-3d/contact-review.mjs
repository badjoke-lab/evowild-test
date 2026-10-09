// Supplemental every-render-frame contact measurement, without video overhead.
// Baseline main.js is supplied from the recorded Git commit; this is explicitly
// a controlled code comparison using the same local Three.js and current UI.
import {chromium,devices} from '@playwright/test';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {gzipSync} from 'node:zlib';
const base='610d42800180ed31f174a097fc2eb96c27ecd0ab';
const root='docs/evidence/gamestudio-3d-20261010';
const probe=await fs.readFile('scripts/gamestudio-3d/probe.js','utf8');
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});
for(const phase of ['before','after'])for(const [device,options] of [['desktop',{viewport:{width:1280,height:720}}],['android',devices['Pixel 7']]]){
  const page=await browser.newPage(options);
  const source=phase==='before'?execFileSync('git',['show',`${base}:public/preview-motion-first/main.js`],{encoding:'utf8',maxBuffer:2**22}):await fs.readFile('public/preview-motion-first/main.js','utf8');
  await page.route('**/preview-motion-first/main.js',route=>route.fulfill({body:source+'\n'+probe,contentType:'text/javascript'}));
  await page.goto('http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?skipStart=1');
  await page.waitForFunction(()=>window.__gameStudioProbe&&document.querySelector('#scene').dataset.runnerCount==='18');
  await page.locator('[data-camera=SIDE]').click();await page.waitForTimeout(3000);
  const samples=await page.evaluate(async()=>{const samples=[];const start=performance.now();await new Promise((resolve,reject)=>{function tick(){try{const s=window.__gameStudioProbe();samples.push({time:s.time,feet:s.feet});if(performance.now()-start<6000)requestAnimationFrame(tick);else resolve();}catch(e){reject(e);}}requestAnimationFrame(tick);});return samples;});
  await fs.writeFile(`${root}/${phase}/${device}/contact-frames.json.gz`,gzipSync(JSON.stringify({referenceSurfaceY:0,method:'Every rendered frame, 6 s, 18 runners; baseline main.js from '+base+'; identical current UI and local Three.js 0.181.0 for both phases. No video, no simulation mutation. Clearance is transformed box bound above track Y=0, not a collision solver.',samples},null,2)));
  console.log(`${phase}/${device}: ${samples.length} contact frames`);
  await page.close();
}
// Actual existing single-proxy review mode: retain 18-runner simulation, isolate
// one visible body. These pictures are diagnostics, NOT normal 18-runner evidence.
const page=await browser.newPage({viewport:{width:1280,height:720}});
for(const [id,morph] of ['S','P','E','A'].entries()){
  await page.goto(`http://127.0.0.1:4173/evowild-test/preview-motion-first-race/index.html?skipStart=1&proxyReviewRunner=${id}`);
  await page.waitForFunction(()=>document.querySelector('#scene').dataset.runnerCount==='18');
  await page.locator('#agentPanel').evaluate(e=>e.open=false);
  for(const camera of ['SIDE','LOW']){
    await page.locator(`[data-camera=${camera}]`).click();await page.waitForTimeout(1700);
    await page.screenshot({path:`${root}/after/desktop/isolated-${morph}-${camera}.png`});
  }
}
await browser.close();

import { chromium, devices } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';

const phase = process.argv[2] || 'after';
const out = path.resolve(process.env.EVIDENCE_DIR || `docs/evidence/gamestudio-3d-20261010/${phase}`);
const origin = process.env.BASE_URL || 'http://127.0.0.1:4173';
const url = `${origin}/evowild-test/preview-motion-first-race/index.html?skipStart=1`;
const bridge = process.env.THREE_BASELINE_DIR;
const baselineCommit = '610d42800180ed31f174a097fc2eb96c27ecd0ab';
const baselineFile = file => execFileSync('git',['show',`${baselineCommit}:${file}`],{encoding:'utf8',maxBuffer:2**22});
const appSource = phase === 'before' ? baselineFile('public/preview-motion-first/main.js') : await fs.readFile('public/preview-motion-first/main.js','utf8');
const probe = await fs.readFile(new URL('./probe.js', import.meta.url), 'utf8');
await fs.mkdir(out, {recursive:true});
const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args:['--no-sandbox','--enable-unsafe-swiftshader']});
const environment = {phase, sourceCommit:phase === 'before' ? baselineCommit : execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
  appSourceSha256:createHash('sha256').update(appSource).digest('hex'),
  footReferenceSurfaceY:0,
  node:process.version, browser:browser.version(), platform:process.platform, architecture:process.arch,
  transportBridge:bridge ? 'Official npm three@0.181.0 files served in place of blocked unpkg requests; app code unchanged.' : null,
  instrumentation:'Read-only module probe at 10 Hz; RAF wall-clock FPS. Video recording enabled. Headless software GPU, not physical Android.',
  cameras:['SIDE','LOW','CHASE','FRONT'], sampleSeconds:5};

if (phase === 'before') {
  const page = await browser.newPage({viewport:{width:1280,height:720}});
  await page.route('**/preview-motion-first-race/index.html?*',route=>route.fulfill({body:baselineFile('public/preview-motion-first-race/index.html'),contentType:'text/html'}));
  const failures=[];
  page.on('requestfailed', r=>failures.push({url:r.url(),error:r.failure()}));
  await page.goto(url); await page.waitForTimeout(2000);
  await page.screenshot({path:path.join(out,'stock-boot-failure.png')});
  await fs.writeFile(path.join(out,'stock-boot-failure.json'),JSON.stringify({failures,dataset:await page.locator('#scene').evaluate(e=>({...e.dataset}))},null,2));
  await page.close();
  if (!bridge) throw new Error('Set THREE_BASELINE_DIR to official npm three@0.181.0 for the controlled baseline capture.');
}

for (const [name, options] of [['desktop',{viewport:{width:1280,height:720}}],['android',devices['Pixel 7']]]) {
  const dir=path.join(out,name); await fs.mkdir(dir,{recursive:true});
  const context=await browser.newContext({...options,recordVideo:{dir,size:options.viewport}});
  if (phase === 'before') await context.route('**/preview-motion-first-race/index.html?*',route=>route.fulfill({body:baselineFile('public/preview-motion-first-race/index.html'),contentType:'text/html'}));
  if (bridge) await context.route('https://unpkg.com/three@0.181.0/**',async route=>{
    const relative=new URL(route.request().url()).pathname.split('/three@0.181.0/')[1];
    await route.fulfill({body:await fs.readFile(path.join(bridge,relative)),contentType:'text/javascript',headers:{'access-control-allow-origin':'*'}});
  });
  await context.route('**/preview-motion-first/main.js',async route=>{
    await route.fulfill({body:appSource+'\n'+probe,contentType:'text/javascript'});
  });
  const page=await context.newPage(); const errors=[]; const requests=[];
  page.on('console',m=>{if(m.type()==='error')errors.push(`${m.text()} (${m.location().url})`);});
  page.on('pageerror',e=>errors.push(e.message)); page.on('requestfailed',r=>errors.push(`${r.url()}: ${r.failure()?.errorText}`));
  page.on('request',r=>requests.push(r.url()));
  await page.goto(url);
  await page.waitForFunction(()=>document.querySelector('#scene')?.dataset.runnerCount==='18');
  await page.waitForTimeout(2500);
  const gl=await page.evaluate(()=>{const c=document.querySelector('canvas').getContext('webgl2');const e=c.getExtension('WEBGL_debug_renderer_info');return {renderer:e?c.getParameter(e.UNMASKED_RENDERER_WEBGL):c.getParameter(c.RENDERER),viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,userAgent:navigator.userAgent};});
  const samples=[]; const segments=[];
  for (const camera of environment.cameras) {
    // Actual median-ranked subject, not a fixed breakaway runner.
    const focus=await page.evaluate(()=>window.__gameStudioProbe().runners.sort((a,b)=>b.distance-a.distance)[8].id);
    await page.locator(`[data-camera="${camera}"]`).click({force:true});
    await page.selectOption('#runnerSelect',String(focus));
    await page.waitForTimeout(1000);
    const segment=await page.evaluate(async()=>{
      const frames=[], samples=[]; let last=performance.now(); const start=last; let next=0;
      await new Promise(resolve=>{function tick(now){frames.push(now-last);last=now;if(now>=next){samples.push(window.__gameStudioProbe());next=now+100;}if(now-start<5000)requestAnimationFrame(tick);else resolve();}requestAnimationFrame(tick);});
      frames.shift();return {start,end:performance.now(),frames,samples};
    });
    await page.screenshot({path:path.join(dir,`${camera.toLowerCase()}.png`)});
    samples.push(...segment.samples); delete segment.samples;
    segments.push({camera,focus,...segment});
  }
  const ui=await page.evaluate(()=>{
    const selectors=['.hud-top .brand','.race-readout','.hud-bottom .control-block','.race-setup > summary','#focusCard','#agentPanel'];
    const boxes=selectors.flatMap(s=>Array.from(document.querySelectorAll(s))).filter(e=>e.checkVisibility()).map(e=>{const r=e.getBoundingClientRect();return {selector:e.id||e.className,x:r.x,y:r.y,width:r.width,height:r.height};});
    let covered=0; for(let y=0;y<innerHeight;y+=4)for(let x=0;x<innerWidth;x+=4)if(boxes.some(b=>x>=b.x&&x<b.x+b.width&&y>=b.y&&y<b.y+b.height))covered+=16;
    return {boxes,coveredFraction:covered/(innerWidth*innerHeight),horizontalOverflow:document.documentElement.scrollWidth>innerWidth};
  });
  // Demonstrate the existing shortcut/input conflict, and verify its repair after.
  await page.locator('#agentPanel').evaluate(e=>{if(e.tagName==='DETAILS')e.open=true;});
  const details=page.locator('#agentDetails');if(await details.count())await details.evaluate(e=>e.open=true);
  await page.locator('#agentOwnerInput').fill('PLAYER');
  const before=await page.evaluate(()=>window.__gameStudioProbe());
  await page.locator('#agentOwnerInput').press('Space');
  await page.locator('#agentOwnerInput').press('Digit2');
  const after=await page.evaluate(()=>window.__gameStudioProbe());
  const inputCheck={beforePaused:before.paused,afterPaused:after.paused,beforeCamera:before.requestedCamera,afterCamera:after.requestedCamera,value:await page.locator('#agentOwnerInput').inputValue()};
  await fs.writeFile(path.join(dir,'raw.json.gz'),gzipSync(JSON.stringify({environment:{...environment,...gl},errors,requests,segments,samples,ui,inputCheck},null,2)));
  const video=page.video();await context.close();await video.saveAs(path.join(dir,'side-low-chase-front.webm'));await video.delete();
  console.log(JSON.stringify({phase,device:name,errors,inputCheck,coverage:ui.coveredFraction,frames:segments.map(s=>({camera:s.camera,fps:1000/(s.frames.reduce((a,b)=>a+b,0)/s.frames.length)}))}));
}
await browser.close();

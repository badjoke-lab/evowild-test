import {chromium} from 'playwright';import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const out=path.resolve(process.argv[2]),browser=await chromium.launch({args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
const page=await browser.newPage({viewport:{width:1000,height:760}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
await page.goto(pathToFileURL(path.join(out,'live-race.html')).href);
await page.waitForFunction(()=>window.__race?.mode==='ready',{},{timeout:60000});
const initial=await page.evaluate(()=>window.__race);if(initial.n<8000||initial.glError)throw Error(JSON.stringify(initial));
await page.screenshot({path:path.join(out,'live-ready.png')});await page.click('#start');await page.waitForFunction(()=>window.__race?.elapsed>.8);
await page.click('#pause');await page.waitForFunction(()=>window.__race?.mode==='paused');
const views={};for(const name of ['side','chase','front','overhead']){await page.click('[data-camera="'+name+'"]');await page.waitForFunction(name=>window.__race?.camera===name,name);await page.screenshot({path:path.join(out,'live-'+name+'.png')});views[name]=await page.evaluate(()=>window.__race)}
await page.click('#pause');await page.click('#start');await page.locator('#boost').hover();await page.mouse.down();await page.waitForFunction(()=>window.__race?.energy<.8);await page.mouse.up();
const moving=await page.evaluate(()=>window.__race);if(moving.playerZ<=-10||moving.glError)throw Error(JSON.stringify(moving));
await page.screenshot({path:path.join(out,'live-running.png')});
await page.waitForFunction(()=>window.__race?.mode==='done',{},{timeout:90000});
const finished=await page.evaluate(()=>window.__race);if(finished.finish.length!==4||new Set(finished.finish).size!==4||finished.glError||errors.length)throw Error(JSON.stringify({finished,errors}));
await page.screenshot({path:path.join(out,'live-finish.png')});
await page.click('#start');await page.waitForFunction(()=>window.__race?.mode==='race'&&window.__race?.finish.length===0);
fs.writeFileSync(path.join(out,'live-browser.json'),JSON.stringify({initial,moving,finished,views,errors,environment:'Chromium software WebGL (SwiftShader); no physical device benchmark'},null,2));console.log('LIVE_BROWSER_PASS',JSON.stringify({n:initial.n,finished:finished.finish,views:Object.keys(views)}));
}finally{await browser.close()}

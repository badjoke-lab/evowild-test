// Assemble review documents/video from actual browser frames; no image synthesis.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {chromium} from '@playwright/test';
const dest='docs/evidence/p-canonical-3d-20261011',scratch='work/p-canonical';
for(const view of ['SIDE','FRONT34']){
 execFileSync('ffmpeg',['-y','-loglevel','error','-framerate','30','-i',`${scratch}/run-frames/${view}-%03d.png`,'-vf','loop=loop=3:size=24:start=0,setpts=N/(30*TB)','-t','3.2','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',`${scratch}/${view}.mp4`]);
}
fs.writeFileSync(`${scratch}/concat.txt`,"file 'SIDE.mp4'\nfile 'FRONT34.mp4'\n");
execFileSync('ffmpeg',['-y','-loglevel','error','-f','concat','-safe','0','-i',`${scratch}/concat.txt`,'-c','copy','-movflags','+faststart',`${dest}/running-review.mp4`]);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1800,height:1180},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:4173/evowild-test/docs/evidence/p-canonical-3d-20261011/comparison.html');
await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));await page.screenshot({path:`${dest}/comparison.png`,fullPage:true});
const rows=['SIDE','FRONT34'].map(view=>`<h2>${view} / 0.8 s cycle</h2><section>${[0,6,12,18].map(f=>`<figure><img src="http://127.0.0.1:4173/evowild-test/${dest}/run-${view}-${String(f).padStart(2,'0')}.png"><figcaption>${(f/30).toFixed(1)} s</figcaption></figure>`).join('')}</section>`).join('');
await page.setContent(`<html><style>body{font:20px system-ui;background:#eef0ee;padding:24px;color:#203039}h1{margin:0}h2{font-size:20px;margin:20px 0 8px}p{font-size:16px}section{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}figure{margin:0;background:white}img{width:100%}figcaption{padding:8px}</style><h1>P / minimal running review</h1><p>Actual GLB rendered in the browser · same geometry as the five rest views · deterministic samples, not an FPS benchmark</p>${rows}</html>`);
await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));await page.screenshot({path:`${dest}/running-contact-sheet.png`,fullPage:true});await browser.close();
console.log('Packaged comparison, running contact sheet, and 6.4 s video');

// Assemble v2 review from actual GLB renders, not generated concept art.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {chromium} from '@playwright/test';
const dest='docs/evidence/p-canonical-3d-v3-20261011',scratch='work/p-canonical-v3';
for (const view of ['SIDE','FRONT34']) {
  execFileSync('ffmpeg',['-y','-loglevel','error','-framerate','30',
    '-i',`${scratch}/run-frames/${view}-%03d.png`,
    '-vf','loop=loop=3:size=24:start=0,setpts=N/(30*TB)',
    '-t','3.2','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',`${scratch}/${view}.mp4`]);
}
fs.writeFileSync(`${scratch}/concat.txt`,"file 'SIDE.mp4'\nfile 'FRONT34.mp4'\n");
execFileSync('ffmpeg',['-y','-loglevel','error','-f','concat','-safe','0',
  '-i',`${scratch}/concat.txt`,'-c','copy','-movflags','+faststart',`${dest}/running-review.mp4`]);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1550,height:1100},deviceScaleFactor:1});
const base='http://127.0.0.1:4173/evowild-test';
const comparison=[
 ['Canonical P','concept/P.webp'],
 ['P v1 / SIDE','docs/evidence/p-canonical-3d-20261011/SIDE.png'],
 ['P v2 / SIDE','docs/evidence/p-canonical-3d-v2-20261011/SIDE.png'],
 ['P v3 / SIDE',dest+'/SIDE.png'],
 ['P v1 / FRONT34','docs/evidence/p-canonical-3d-20261011/FRONT34.png'],
 ['P v2 / FRONT34','docs/evidence/p-canonical-3d-v2-20261011/FRONT34.png'],
 ['P v3 / FRONT34',dest+'/FRONT34.png'],
 ['P v3 / BACK',dest+'/BACK.png']
];
function html(title,rows){
 return '<!doctype html><html><meta charset="utf-8"><style>body{font:18px system-ui;background:#edf1f2;color:#183039;padding:16px}main{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0;background:white;padding:8px}img{width:100%;height:280px;object-fit:contain}figcaption{font-weight:600;padding:7px}</style><h1>'+title+'</h1><p>Actual reference and GLB renders · matching asset files · visual approval not implied</p><main>'+rows.map(([n,p])=>'<figure><img src="'+base+'/'+p+'"><figcaption>'+n+'</figcaption></figure>').join('')+'</main></html>';
}
await page.setContent(html('P shape review / canonical · v1 · v2 · v3',comparison));
await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
await page.screenshot({path:dest+'/comparison-v1-v2-v3.png',fullPage:true});
const rows=['SIDE','FRONT34'].flatMap(view=>[0,6,12,18].map(f=>[view+' / '+(f/30).toFixed(1)+'s',dest+'/run-'+view+'-'+String(f).padStart(2,'0')+'.png']));
await page.setContent(html('P v3 / minimal running study',rows));
await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
await page.screenshot({path:dest+'/running-contact-sheet.png',fullPage:true});
await browser.close();
console.log('P v3 review evidence packaged');

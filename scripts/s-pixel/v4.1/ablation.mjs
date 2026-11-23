// Isolate the work saved by rounding fully covered/empty Bayer endpoints.
// Hold the repaired surface, view bins, programs, camera and sprites constant.
import {openLab,DEMO} from '../browser.mjs';
import path from 'node:path';
import fs from 'node:fs/promises';
process.env.LAB_URL=(process.env.LAB_BASE_URL||'http://127.0.0.1:4173/s-pixel-lab/')+'v4.1/';
const {page,browser,errors}=await openLab({width:1280,height:900});
try{
 const rows=await page.evaluate(async()=>{
  const {sampleRace}=await import('./device-benchmark.js');
  const lab=window.sLab,r=lab.renderer;
  lab.manual(true);
  r.fixedRaster={width:877,height:414};
  const rows=[];
  for(const order of [['all','skip'],['skip','all'],['all','skip']]){
   for(const coverage of order){
    if(coverage==='all')r.effectiveCoverage=f=>f;
    else delete r.effectiveCoverage;
    const trial=await sampleRace(lab,'mixed100',r.fixedRaster,()=>{},new AbortController().signal);
    rows.push({coverage,...trial});
   }
  }
  return rows;
 });
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(path.join(DEMO,'v4.1/evidence/coverage-ab.json'),JSON.stringify(rows)+'\n');
}finally{await browser.close();}

// Pixel evidence complements visual review; these measurements do not prove
// anatomical identity or horizontal foot locking.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {chromium} from '@playwright/test';
const evidence='docs/evidence/p-revision-20261011';
const paths={old:`${evidence}/old-12-phase.webp`,revised:'public/concept/p-run-sheet.webp'};
const sources=Object.fromEntries(Object.entries(paths).map(([key,file])=>[key,`data:image/webp;base64,${fs.readFileSync(file).toString('base64')}`]));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{
 const page=await browser.newPage();
 await page.route('https://p-review.invalid/',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>P pixel audit</title>'}));
 await page.goto('https://p-review.invalid/');
 const audit=await page.evaluate(async sources=>{
  const result={};
  for(const [version,src] of Object.entries(sources)){
   const im=new Image();im.src=src;await im.decode();const c=document.createElement('canvas');c.width=416;c.height=320;const ctx=c.getContext('2d',{willReadFrequently:true}),frames=[],masks=[];
   for(let i=0;i<12;i++){
    ctx.clearRect(0,0,416,320);ctx.drawImage(im,i%4*416,Math.floor(i/4)*320,416,320,0,0,416,320);
    const p=ctx.getImageData(0,0,416,320).data,mask=new Uint8Array(416*320),groundXs=[];let l=416,r=0,t=320,b=0,area=0,cx=0,cy=0,cn=0;
    for(let k=0;k<mask.length;k++)if(p[k*4+3]>12){const x=k%416,y=Math.floor(k/416);mask[k]=1;area++;l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);if(p[k*4+1]>140&&p[k*4+2]>145&&p[k*4]<p[k*4+1]*.73){cx+=x;cy+=y;cn++;}}
    for(let x=0;x<416;x++){let n=0;for(let y=291;y<=295;y++)n+=mask[y*416+x];if(n>=2)groundXs.push(x);}
    const bands=[];for(const x of groundXs){const band=bands.at(-1);if(!band||x-band[1]>7)bands.push([x,x]);else band[1]=x;}
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',p)),x=>x.toString(16).padStart(2,'0')).join('');
    frames.push({phase:i+1,bounds:[l,t,r,b],clearance:295-b,opaquePixels:area,headCue:[cx/cn,cy/cn],groundBands:bands,hash:digest});masks.push(mask);
   }
   const transitions=frames.map((f,i)=>{
    const j=(i+1)%12;let inter=0,union=0,lowInter=0,lowUnion=0;
    for(let k=0;k<masks[i].length;k++){const a=masks[i][k],b=masks[j][k];inter+=a&&b?1:0;union+=a||b?1:0;if(k>=190*416){lowInter+=a&&b?1:0;lowUnion+=a||b?1:0;}}
    return {from:i+1,to:j+1,silhouetteIoU:inter/union,lowerBodyIoU:lowInter/lowUnion,headCueDisplacement:Math.hypot(f.headCue[0]-frames[j].headCue[0],f.headCue[1]-frames[j].headCue[1])};
   });result[version]={frames,transitions,wrap:transitions[11]};
  }return result;
 },sources);
 const expected=[0,0,0,0,8,16,24,12,4,0,0,0];
 assert.deepEqual(audit.revised.frames.map(f=>f.clearance),expected);
 assert.equal(new Set(audit.revised.frames.map(f=>f.hash)).size,12);
 for(const f of audit.revised.frames){assert.ok(f.bounds[0]>12&&f.bounds[2]<404&&f.bounds[1]>12);if(f.clearance===0)assert.ok(f.groundBands.length>0);}
 assert.ok(audit.revised.wrap.lowerBodyIoU>audit.old.wrap.lowerBodyIoU,'wrap must improve lower-limb continuity');
 audit.scope='Alpha bounds/contact bands and adjacent silhouettes. Not a biomechanical or world-space no-slip certificate.';
 audit.hashes=Object.fromEntries(Object.entries(paths).map(([k,p])=>[k,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]));
 fs.writeFileSync(`${evidence}/contact-loop-audit.json`,JSON.stringify(audit,null,2)+'\n');
 console.log(JSON.stringify({oldWrap:audit.old.wrap,newWrap:audit.revised.wrap,clearances:audit.revised.frames.map(f=>f.clearance),groundBands:audit.revised.frames.map(f=>f.groundBands)}));
}finally{await browser.close();}

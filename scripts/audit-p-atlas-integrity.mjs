// Examine actual production P RGBA pixels for non-canonical neon streaks.
// This does NOT edit or accept/reject anatomy. Visual review remains essential.
import fs from 'node:fs';
import {chromium} from '@playwright/test';
const refFile='public/concept/P.webp',pFile='public/concept/p-run-sheet.webp';
const dest='docs/evidence/p-atlas-integrity-20261012';
fs.mkdirSync(dest,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox'],
 executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium'});
try {
 const page=await browser.newPage();
 await page.goto('about:blank');
 const results=await page.evaluate(async ({src,ref})=>{
  const load=async u=>{let i=new Image();i.src=u;await i.decode();return i};
  const im=await load(src),canonical=await load(ref);
  const c=document.createElement('canvas');c.width=im.width;c.height=im.height;
  const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(im,0,0);
  const rgba=ctx.getImageData(0,0,c.width,c.height),raw=rgba.data;
  if(c.width!==1664||c.height!==960)throw Error('Unexpected P atlas dimensions');
  const overlay=document.createElement('canvas');overlay.width=c.width;overlay.height=c.height;
  const cx=overlay.getContext('2d');
  cx.fillStyle='#dce4e8';cx.fillRect(0,0,overlay.width,overlay.height);cx.drawImage(im,0,0);
  const smudge=document.createElement('canvas');smudge.width=c.width;smudge.height=c.height;
  const sx=smudge.getContext('2d'),mask=sx.createImageData(c.width,c.height);
  const frames=[],stats={magenta:0,blue:0,green:0,highChroma:0};
  for(let i=0;i<12;i++){
   const ox=(i%4)*416,oy=Math.floor(i/4)*320;
   let n=0,nontransparent=0,anomaly=0,mg=0,bl=0,gn=0;
   let minx=416,miny=320,maxx=-1,maxy=-1;
   const yBins=new Array(16).fill(0);
   for(let y=0;y<320;y++)for(let x=0;x<416;x++){
    const p=((oy+y)*1664+ox+x)*4;
    const a=raw[p+3],r=raw[p],g=raw[p+1],b=raw[p+2];
    if(a<=12)continue;
    nontransparent++;
    const eye=(x>=287&&x<=356&&y>=55&&y<=135);
    const magenta=r>=65&&b>=55&&r>g*1.55&&b>g*1.43&&b>r*.40;
    const cyanBlue=b>=105&&b>r*1.5&&b>g*1.12;
    const green=g>=85&&g>r*1.22&&g>b*.75;
    const isAnomaly=(magenta||cyanBlue||green)&&!eye;
    if(!isAnomaly)continue;
    anomaly++;mg+=magenta?1:0;bl+=cyanBlue?1:0;gn+=green?1:0;
    yBins[Math.floor(y/20)]++;
    minx=Math.min(minx,x);miny=Math.min(miny,y);maxx=Math.max(maxx,x);maxy=Math.max(maxy,y);
    const k=p;mask.data[k]=255;mask.data[k+1]=230;mask.data[k+2]=0;mask.data[k+3]=215;
   }
   if(anomaly>0){
    cx.strokeStyle='#fcee23';cx.lineWidth=2;
    cx.strokeRect(ox+minx,oy+miny,maxx-minx+1,maxy-miny+1);
   }
   cx.fillStyle='#17222f';cx.fillRect(ox+8,oy+7,195,25);
   cx.font='16px monospace';cx.fillStyle='#fafffb';
   cx.fillText('P '+String(i+1).padStart(2,'0')+' neon:'+anomaly,ox+13,oy+25);
   frames.push({phase:i+1,visibleAlphaPixels:nontransparent,suspectPixels:anomaly,
    fractionOfVisible:nontransparent?anomaly/nontransparent:0,
    detected:{magenta:mg,blue:bl,green:gn},
    boundingBox:anomaly?[minx,miny,maxx,maxy]:null,verticalBins20px:yBins});
  }
  sx.putImageData(mask,0,0);
  cx.drawImage(smudge,0,0);
  const compare=document.createElement('canvas');compare.width=1248;compare.height=450;
  const q=compare.getContext('2d');q.fillStyle='#dce4e8';q.fillRect(0,0,1248,450);
  q.fillStyle='#1b2d39';q.font='22px sans-serif';q.fillText('Canonical P (unchanged)',15,32);
  q.fillText('P atlas / sample phase 1',431,32);q.fillText('Suspect pixel overlay',847,32);
  q.drawImage(canonical,0,45,416,325);
  q.drawImage(im,0,0,416,320,416,45,416,320);
  q.drawImage(overlay,0,0,416,320,832,45,416,320);
  return {stats:{imageSize:[c.width,c.height],frames,
    totalSuspect:frames.reduce((a,b)=>a+b.suspectPixels,0),
    totalVisible:frames.reduce((a,b)=>a+b.visibleAlphaPixels,0),
    method:'RGBA alpha>12, conservative magenta/blue/green anomaly families; protect cyan eye box; not an anatomical or source-identity validator',
    caveat:'Counts can include legitimate cool/warm antialias pixels and miss dark streaks; review overlaid masks before cleaning.'},
    overlay:overlay.toDataURL('image/png'),comparison:compare.toDataURL('image/png')};
 },{src:'data:image/webp;base64,'+fs.readFileSync(pFile).toString('base64'),ref:'data:image/webp;base64,'+fs.readFileSync(refFile).toString('base64')});
 for(const [k,f] of [['overlay','atlas-chroma-anomaly-overlay.png'],['comparison','reference-vs-artifact-example.png']])
  fs.writeFileSync(dest+'/'+f,Buffer.from(results[k].split(',')[1],'base64'));
 fs.writeFileSync(dest+'/stats.json',JSON.stringify(results.stats,null,2)+'\n');
 console.log('P_ATLAS_CHROMA_ANOMALY',JSON.stringify({total:results.stats.totalSuspect,visible:results.stats.totalVisible,perPhase:results.stats.frames.map(x=>x.suspectPixels)}));
 if(results.stats.totalSuspect<=0)throw Error('Expected detected visible anomalies: inspect threshold and image source');
}finally{await browser.close()}

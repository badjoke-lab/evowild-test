import fs from 'node:fs';
import {chromium} from '@playwright/test';
import {spawn} from 'node:child_process';
const out='docs/evidence/p-layered-20261012';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage();
 await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html?selected=2',{waitUntil:'networkidle'});
 const data=await page.evaluate(async()=>{
  const {loadPLayered,drawPLayered}=await import('/evowild-test/src/p_layered.js');await loadPLayered('/evowild-test/');
  const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
  const sheet=canvas(1664,960),contact=canvas(1664,1080),sc=sheet.getContext('2d'),cx=contact.getContext('2d');
  cx.fillStyle='#e8eef0';cx.fillRect(0,0,1664,1080);const frames=[],poses=[];
  for(let i=0;i<12;i++){
   const c=canvas(416,320),x=c.getContext('2d'),r={distance:100,phaseOffset:0};
   const pose=drawPLayered(x,r,{x:208,y:296,width:416,ppm:10,projectX:m=>208+(m-100)*10,groundY:()=>296,lane:1.5,time:0,reviewPhase:i/12});
   frames.push(c);poses.push({phase:i+1,feet:pose.feet,bob:pose.bob,pitch:pose.pitch});
   sc.drawImage(c,i%4*416,Math.floor(i/4)*320);const yy=Math.floor(i/4)*360;cx.drawImage(c,i%4*416,yy);
   cx.strokeStyle='#91a5af';cx.beginPath();cx.moveTo(i%4*416+8,yy+296);cx.lineTo(i%4*416+408,yy+296);cx.stroke();
   cx.fillStyle='#203844';cx.font='16px sans-serif';cx.fillText(`${String(i+1).padStart(2,'0')}  ${pose.feet.filter(f=>f.stance).map(f=>f.id).join(' + ')}`,i%4*416+10,yy+337);
  }
  const load=async url=>{const im=new Image();im.src=url;await im.decode();return im;};
  const canonical=await load('/evowild-test/concept/P.webp'),oldSheet=await load('/evowild-test/concept/p-run-sheet.webp');
  const old=canvas(416,320);old.getContext('2d').drawImage(oldSheet,0,0,416,320,0,0,416,320);
  const neutral=canvas(416,320);
  drawPLayered(neutral.getContext('2d'),{distance:100,phaseOffset:0},{x:208,y:296,width:416,ppm:10,projectX:m=>208+(m-100)*10,groundY:()=>296,lane:1.5,time:0,reviewPhase:0,neutral:true});
  const compare=canvas(1664,610),cc=compare.getContext('2d');cc.fillStyle='#e8eef0';cc.fillRect(0,0,1664,610);
  [canonical,old,neutral,frames[0]].forEach((im,i)=>{
   const c=canvas(im.width,im.height),x=c.getContext('2d');x.drawImage(im,0,0);const p=x.getImageData(0,0,c.width,c.height).data;let l=c.width,r=0,t=c.height,b=0;
   for(let k=0;k<p.length/4;k++)if(p[k*4+3]>12){l=Math.min(l,k%c.width);r=Math.max(r,k%c.width);t=Math.min(t,Math.floor(k/c.width));b=Math.max(b,Math.floor(k/c.width));}
   const w=r-l+1,h=b-t+1,H=370*h/w;cc.save();cc.translate(i*416+(i===0?393:23),390-H);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,370,H);cc.restore();
   x.globalCompositeOperation='source-in';x.fillStyle='#1d3542';x.fillRect(0,0,c.width,c.height);cc.save();cc.translate(i*416+(i===0?263:153),450);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,110,110*h/w);cc.restore();
   cc.fillStyle='#203844';cc.font='20px sans-serif';cc.fillText(['CANONICAL P (mirrored)','CURRENT 12 / 9aeed97','LAYERED P / REST','LAYERED P / RUN'][i],i*416+16,30);
  });
  cc.font='16px sans-serif';cc.fillText('Equal full-creature width; aspect preserved. Bottom silhouettes: 110px.',20,420);
  return {sheet:sheet.toDataURL(),contact:contact.toDataURL(),comparison:compare.toDataURL(),poses};
 });
 const write=(name,url)=>fs.writeFileSync(`${out}/${name}`,Buffer.from(url.split(',')[1],'base64'));
 write('layered-12-phase.png',data.sheet);write('layered-contact-sheet.png',data.contact);write('canonical-old-layered.png',data.comparison);
 fs.writeFileSync(`${out}/phase-poses.json`,JSON.stringify(data.poses,null,2)+'\n');
 await new Promise((resolve,reject)=>{const p=spawn('magick',[`${out}/layered-12-phase.png`,'-define','webp:lossless=true',`${out}/layered-12-phase.webp`],{stdio:'inherit'});p.on('error',reject);p.on('close',c=>c?reject(Error(c)):resolve());});
}finally{await browser.close();}

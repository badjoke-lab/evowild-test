import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {chromium} from '@playwright/test';
const dir='docs/evidence/p-rig-v2-20261013',scratch='work/p-rig-v2';
const before='c648a95d61529df3501f8cd11dc65d0712b0fd7e';
fs.mkdirSync(`${scratch}/before-assets/concept/p-layered`,{recursive:true});
const stableWrite=(path,bytes)=>{if(!fs.existsSync(path)||!fs.readFileSync(path).equals(bytes))fs.writeFileSync(path,bytes);};
stableWrite(`${scratch}/before-rig.js`,execFileSync('git',['show',`${before}:src/p_layered.js`]));
for(const path of execFileSync('git',['ls-tree','-r','--name-only',before,'public/concept/p-layered'],{encoding:'utf8'}).trim().split('\n'))
 stableWrite(`${scratch}/before-assets/concept/p-layered/${path.split('/').at(-1)}`,execFileSync('git',['show',`${before}:${path}`]));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage();await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html');
 const data=await page.evaluate(async()=>{
  const current=await import('/evowild-test/src/p_layered.js');
  const old=await import('/evowild-test/work/p-rig-v2/before-rig.js');
  await current.loadPLayered('/evowild-test/');await old.loadPLayered('/evowild-test/work/p-rig-v2/before-assets/');
  const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
  const pose=(module,phase,neutral=false)=>{
   const image=canvas(416,320),ctx=image.getContext('2d');
   const result=module.drawPLayered(ctx,{distance:100,phaseOffset:0},{x:208,y:296,width:416,ppm:10,
    projectX:m=>208+(m-100)*10,groundY:()=>296,lane:1.5,time:0,reviewPhase:phase,neutral});
   return {image,result};
  };
  const sheet=canvas(1664,960),contact=canvas(1664,1080),cx=contact.getContext('2d'),frames=[],poses=[];
  cx.fillStyle='#e8eef0';cx.fillRect(0,0,contact.width,contact.height);
  for(let i=0;i<12;i++){
   const p=pose(current,i/12);frames.push(p.image);
   poses.push({phase:i+1,feet:p.result.feet,bob:p.result.bob,pitch:p.result.pitch,bodyOffset:p.result.bodyOffset,flight:p.result.flight});
   sheet.getContext('2d').drawImage(p.image,i%4*416,Math.floor(i/4)*320);
   const x=i%4*416,y=Math.floor(i/4)*360;cx.drawImage(p.image,x,y);
   cx.strokeStyle='#839aa5';cx.beginPath();cx.moveTo(x+8,y+296);cx.lineTo(x+408,y+296);cx.stroke();
   cx.fillStyle='#203844';cx.font='16px sans-serif';cx.fillText(`${i+1} ${p.result.feet.filter(f=>f.stance).map(f=>f.id).join(' + ')||'FLIGHT'}`,x+10,y+337);
  }
  const canonical=new Image();canonical.src='/evowild-test/concept/P.webp';await canonical.decode();
  const compare=canvas(2080,620),cc=compare.getContext('2d');cc.fillStyle='#e8eef0';cc.fillRect(0,0,compare.width,compare.height);
  [canonical,pose(old,0,true).image,pose(old,0).image,pose(current,0,true).image,frames[0]].forEach((im,i)=>{
   const c=canvas(im.width,im.height),x=c.getContext('2d');x.drawImage(im,0,0);
   const pixels=x.getImageData(0,0,c.width,c.height).data;let l=c.width,r=0,t=c.height,b=0;
   for(let k=0;k<pixels.length/4;k++)if(pixels[k*4+3]>12){l=Math.min(l,k%c.width);r=Math.max(r,k%c.width);t=Math.min(t,Math.floor(k/c.width));b=Math.max(b,Math.floor(k/c.width));}
   const w=r-l+1,h=b-t+1,H=370*h/w;
   cc.save();cc.translate(i*416+(i===0?393:23),395-H);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,370,H);cc.restore();
   x.globalCompositeOperation='source-in';x.fillStyle='#1d3542';x.fillRect(0,0,c.width,c.height);
   cc.save();cc.translate(i*416+(i===0?263:153),460);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,110,110*h/w);cc.restore();
   cc.fillStyle='#203844';cc.font='20px sans-serif';cc.fillText(['CANONICAL P','c648a95 REST','c648a95 RUN','REVISED REST','REVISED RUN'][i],i*416+16,30);
  });
  cc.font='16px sans-serif';cc.fillText('Equal full-creature width; aspect preserved. Silhouettes: 110px.',20,425);
  const detail=canvas(1200,650),dc=detail.getContext('2d');dc.fillStyle='#e8eef0';dc.fillRect(0,0,1200,650);
  for(let row=0;row<2;row++){
   const p=pose(row?current:old,5/12);
   ['fore-near','hind-near'].forEach((id,col)=>{
    const knee=p.result.feet.find(f=>f.id===id).knee;
    dc.drawImage(p.image,knee.x-35,knee.y-35,70,70,col*600+20,row*325+40,280,280);
    dc.drawImage(p.image,416-416,0,416,320,col*600+320,row*325+40,260,200);
    dc.fillStyle='#203844';dc.font='18px sans-serif';dc.fillText(`${row?'REVISED':'c648a95'} ${id} joint / same-source crop x4`,col*600+15,row*325+25);
   });
  }
  return {sheet:sheet.toDataURL(),contact:contact.toDataURL(),comparison:compare.toDataURL(),detail:detail.toDataURL(),poses};
 });
 for(const [key,name] of [['sheet','layered-12-phase.png'],['contact','layered-contact-sheet.png'],['comparison','canonical-old-new.png'],['detail','joint-comparison.png']])
  fs.writeFileSync(`${dir}/${name}`,Buffer.from(data[key].split(',')[1],'base64'));
 fs.writeFileSync(`${dir}/phase-poses.json`,JSON.stringify(data.poses,null,2)+'\n');
 execFileSync('magick',[`${dir}/layered-12-phase.png`,'-define','webp:lossless=true',`${dir}/layered-12-phase.webp`]);
}finally{await browser.close();}

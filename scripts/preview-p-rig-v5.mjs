import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {chromium} from '@playwright/test';
const dir='docs/evidence/p-rig-v5-20261015',scratch='work/p-rig-v5';
const before='6c0c79868b14023bba58db6d2fcd5a15cc678f1f';
fs.mkdirSync(`${scratch}/before-assets/concept/p-layered-v5`,{recursive:true});
const stableWrite=(path,bytes)=>{if(!fs.existsSync(path)||!fs.readFileSync(path).equals(bytes))fs.writeFileSync(path,bytes);};
stableWrite(`${scratch}/before-rig.js`,execFileSync('git',['show',`${before}:src/p_layered.js`]));
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage();await page.route("**/src/p_layered.js*",r=>r.fulfill({status:200,contentType:"application/javascript",body:fs.readFileSync("src/p_layered.js","utf8")}));await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html');
 const data=await page.evaluate(async()=>{
  const current=await import('/evowild-test/src/p_layered.js');
  const old=await import('/evowild-test/work/p-rig-v5/before-rig.js');
  const atlas=await current.loadPLayered('/evowild-test/');await old.loadPLayered('/evowild-test/');
  if(!atlas.parts.chest)throw Error('Expected v5 materials; restart stale dev server');
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
   poses.push({phase:i+1,feet:p.result.feet,bob:p.result.bob,pitch:p.result.pitch,bodyOffset:p.result.bodyOffset,flight:p.result.flight,spine:p.result.spine});
   sheet.getContext('2d').drawImage(p.image,i%4*416,Math.floor(i/4)*320);
   const x=i%4*416,y=Math.floor(i/4)*360;cx.drawImage(p.image,x,y);
   cx.strokeStyle='#839aa5';cx.beginPath();cx.moveTo(x+8,y+296);cx.lineTo(x+408,y+296);cx.stroke();
   cx.fillStyle='#203844';cx.font='16px sans-serif';cx.fillText(`${i+1} ${p.result.feet.filter(f=>f.stance).map(f=>f.id).join(' + ')||'FLIGHT'}`,x+10,y+337);
  }
  const canonical=new Image();canonical.src='/evowild-test/concept/P.webp';await canonical.decode();
  const silhouettes=[];
  const compare=canvas(2080,620),cc=compare.getContext('2d');cc.fillStyle='#e8eef0';cc.fillRect(0,0,compare.width,compare.height);
  [canonical,pose(old,0,true).image,pose(old,0).image,pose(current,0,true).image,frames[0]].forEach((im,i)=>{
   const c=canvas(im.width,im.height),x=c.getContext('2d');x.drawImage(im,0,0);
   const pixels=x.getImageData(0,0,c.width,c.height).data;let l=c.width,r=0,t=c.height,b=0;
   for(let k=0;k<pixels.length/4;k++)if(pixels[k*4+3]>12){l=Math.min(l,k%c.width);r=Math.max(r,k%c.width);t=Math.min(t,Math.floor(k/c.width));b=Math.max(b,Math.floor(k/c.width));}
   const w=r-l+1,h=b-t+1,H=370*h/w;
   silhouettes.push({name:['canonical','v4-rest','v4-run','v5-rest','v5-run'][i],alphaBounds:{x:l,y:t,width:w,height:h},heightToWidth:h/w});
   cc.save();cc.translate(i*416+(i===0?393:23),395-H);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,370,H);cc.restore();
   x.globalCompositeOperation='source-in';x.fillStyle='#1d3542';x.fillRect(0,0,c.width,c.height);
   cc.save();cc.translate(i*416+(i===0?263:153),460);if(i===0)cc.scale(-1,1);cc.drawImage(c,l,t,w,h,0,0,110,110*h/w);cc.restore();
   cc.fillStyle='#203844';cc.font='20px sans-serif';cc.fillText(['CANONICAL P','v4 REST','v4 RUN','v5 REST','v5 RUN'][i],i*416+16,30);
  });
  cc.font='16px sans-serif';cc.fillText('Equal full-creature width; aspect preserved. Silhouettes: 110px.',20,425);
  const detail=canvas(1200,650),dc=detail.getContext('2d');dc.fillStyle='#e8eef0';dc.fillRect(0,0,1200,650);
  for(let row=0;row<2;row++){
   const p=pose(row?current:old,5/12);
   ['fore-near','hind-near'].forEach((id,col)=>{
    const knee=p.result.feet.find(f=>f.id===id).knee;
    dc.drawImage(p.image,knee.x-35,knee.y-35,70,70,col*600+20,row*325+40,280,280);
    dc.drawImage(p.image,416-416,0,416,320,col*600+320,row*325+40,260,200);
    dc.fillStyle='#203844';dc.font='18px sans-serif';dc.fillText(`${row?'v5':'v4'} ${id} joint / same-source crop x4`,col*600+15,row*325+25);
   });
  }
  const all=canvas(1664,2160),ac=all.getContext('2d');ac.fillStyle='#e8eef0';ac.fillRect(0,0,all.width,all.height);
  const crops=canvas(1440,1440),fc=crops.getContext('2d');fc.fillStyle='#e8eef0';fc.fillRect(0,0,crops.width,crops.height);
  const poseDeltas=[];
  for(let i=0;i<12;i++){
   const before=pose(old,i/12),after=pose(current,i/12);
   for(const [j,p] of [before,after].entries()){
    const x=(i%2)*832+j*416,y=Math.floor(i/2)*360;
    ac.drawImage(p.image,x,y+30);ac.fillStyle='#203844';ac.font='18px sans-serif';ac.fillText(`phase ${i+1} / ${j?'v5':'v4'}`,x+12,y+23);
   }
   poseDeltas.push({phase:i+1,maxJointDelta:Math.max(...after.result.feet.flatMap((f,k)=>['hip','knee','ankle'].map(j=>Math.hypot(f[j].x-before.result.feet[k][j].x,f[j].y-before.result.feet[k][j].y))))});
  }
  for(const [row,index] of [2,3,5,9].entries())for(const [col,module] of [old,current].entries()){
   const p=pose(module,index/12);
   fc.fillStyle='#203844';fc.font='20px sans-serif';fc.fillText(`${col?'v5':'v4'} phase ${index+1}: forelimbs / claws, x3`,col*720+12,row*360+27);
   fc.drawImage(p.image,140,185,230,108,col*720+15,row*360+35,690,324);
  }
  const parts=canvas(1500,1050),pc=parts.getContext('2d');pc.fillStyle='#e8eef0';pc.fillRect(0,0,parts.width,parts.height);
  const names=['fore-upper','fore-lower','chest','fore-paw','fore-far-paw','hind-upper','hind-lower','chest','hind-paw','hind-far-paw'];
  names.forEach((name,i)=>{
   const p=atlas.parts[name],im=p.bitmap,s=Math.min(260/im.width,360/im.height),x=i%5*300,y=Math.floor(i/5)*490;
   pc.drawImage(im,x+(300-im.width*s)/2,y+50,im.width*s,im.height*s);
   pc.fillStyle='#203844';pc.font='18px sans-serif';pc.fillText(name,x+10,y+25);
  });
  pc.font='18px sans-serif';pc.fillText('Authored v5 muscle surfaces; no flat end tint. v4 foot bitmaps and fixed bones retained.',20,1020);
  return {sheet:sheet.toDataURL(),contact:contact.toDataURL(),comparison:compare.toDataURL(),detail:detail.toDataURL(),all:all.toDataURL(),fore: crops.toDataURL(),parts:parts.toDataURL(),poses,poseDeltas,silhouettes};
 });
 for(const [key,name] of [['sheet','layered-12-phase.png'],['contact','layered-contact-sheet.png'],['comparison','canonical-old-new.png'],['detail','joint-comparison.png'],['all','12-phase-before-after.png'],['fore','forelimb-overlap-comparison.png'],['parts','runtime-parts.png']])
  fs.writeFileSync(`${dir}/${name}`,Buffer.from(data[key].split(',')[1],'base64'));
 fs.writeFileSync(`${dir}/silhouette-proportions.json`,JSON.stringify(data.silhouettes,null,2)+'\n');
 fs.writeFileSync(`${dir}/phase-poses.json`,JSON.stringify(data.poses,null,2)+'\n');
 fs.writeFileSync(`${dir}/phase-geometry-comparison.json`,JSON.stringify(data.poseDeltas,null,2)+'\n');

 execFileSync('magick',[`${dir}/layered-12-phase.png`,'-define','webp:lossless=true',`${dir}/layered-12-phase.webp`]);
}finally{await browser.close();}

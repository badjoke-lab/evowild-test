// Pack the reviewed P drawings. No blended frames, optical flow, mesh warps,
// per-frame scaling, or repainting: alpha extraction and rigid placement only.
import fs from 'node:fs';
import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';

const evidence = 'docs/evidence/p-revision-20261011';
const scratch = 'work/p-revision';
const output = process.argv[2] || `${scratch}/candidate.webp`;
const sourceOrder = Array.from({length:12},(_,i)=>i);
const clearance = [0,0,0,0,8,16,24,12,4,0,0,0];
const phases = ['CONTACT','LOAD','PUSH','TOE-OFF','LIFT','GATHER','FLIGHT','EXTEND','REACH','TOUCHDOWN','LOAD','SETTLE'];
const url = file => `data:image/${file.endsWith('.webp')?'webp':'png'};base64,${fs.readFileSync(file).toString('base64')}`;
const command = (exe,args) => new Promise((resolve,reject) => {
  const p=spawn(exe,args,{stdio:'inherit'});p.on('error',reject);p.on('close',code=>code===0?resolve():reject(new Error(`${exe}: ${code}`)));
});
fs.mkdirSync(scratch,{recursive:true});
const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox'],headless:true});
try {
  const page=await browser.newPage();
  const result=await page.evaluate(async ({raw,old,canonical,sourceOrder,clearance,phases})=>{
    const load=async src=>{const i=new Image();i.src=src;await i.decode();return i;};
    const canvas=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
    const source=await load(raw),previous=await load(old),ref=await load(canonical);
    const c=canvas(source.width,source.height),cx=c.getContext('2d',{willReadFrequently:true});cx.drawImage(source,0,0);
    const a=cx.getImageData(0,0,c.width,c.height).data,seen=new Uint8Array(c.width*c.height),q=new Int32Array(seen.length),components=[];
    for(let seed=0;seed<seen.length;seed++){
      if(seen[seed]||a[seed*4+3]<=12)continue;
      let head=0,n=1,l=c.width,r=0,t=c.height,b=0,cueX=0,cueY=0,cueN=0;
      q[0]=seed;seen[seed]=1;
      while(head<n){const p=q[head++],x=p%c.width,y=Math.floor(p/c.width);l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);
        if(a[p*4+1]>140&&a[p*4+2]>145&&a[p*4]<a[p*4+1]*.73){cueX+=x;cueY+=y;cueN++;}
        for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const nx=x+dx,ny=y+dy,k=ny*c.width+nx;if(nx<0||ny<0||nx>=c.width||ny>=c.height||seen[k]||a[k*4+3]<=12)continue;seen[k]=1;q[n++]=k;}
      }
      if(n<1000)continue;
      if(l===0||r===c.width-1||t===0||b===c.height-1)throw new Error(`Source creature touches canvas boundary: ${[l,t,r,b]}`);
      if(cueN<8)throw new Error('Missing head cue anchor');
      const crop=canvas(r-l+1,b-t+1),cc=crop.getContext('2d'),data=cc.createImageData(crop.width,crop.height);
      for(const p of q.slice(0,n)){const k=((Math.floor(p/c.width)-t)*crop.width+p%c.width-l)*4;data.data.set(a.slice(p*4,p*4+4),k);}
      cc.putImageData(data,0,0);components.push({crop,bounds:[l,t,r+1,b+1],pixels:n,cue:[cueX/cueN-l,cueY/cueN-t]});
    }
    components.sort((a,b)=>Math.floor((a.bounds[1]+a.bounds[3])/2/(source.height/3))-Math.floor((b.bounds[1]+b.bounds[3])/2/(source.height/3))||a.bounds[0]-b.bounds[0]);
    if(components.length!==12)throw new Error(`Expected twelve complete drawings; found ${components.length}`);
    const widths=components.map(p=>p.crop.width).sort((a,b)=>a-b);
    const sharedScale=355/((widths[5]+widths[6])/2);
    const frames=[],oldFrames=[],audit=[],sheet=canvas(1664,960),sc=sheet.getContext('2d');
    sourceOrder.forEach((sourceIndex,i)=>{
      const part=components[sourceIndex],f=canvas(416,320),fc=f.getContext('2d');
      // A shared head-cue x anchor avoids bbox-width changes shifting the torso.
      const w=Math.round(part.crop.width*sharedScale),h=Math.round(part.crop.height*sharedScale);
      const scaled=canvas(w,h),scaledCtx=scaled.getContext('2d');scaledCtx.drawImage(part.crop,0,0,w,h);
      const scaledPixels=scaledCtx.getImageData(0,0,w,h).data;
      let lastOpaqueRow=-1;
      for(let p=0;p<w*h;p++)if(scaledPixels[p*4+3]>12)lastOpaqueRow=Math.floor(p/w);
      const x=Math.round(330-part.cue[0]*sharedScale),y=295-clearance[i]-lastOpaqueRow;
      if(x<12||x+w>404||y<12)throw new Error(`Insufficient gutter in frame ${i+1}: ${x},${y},${part.crop.width}`);
      fc.drawImage(scaled,x,y);sc.drawImage(f,i%4*416,Math.floor(i/4)*320);frames.push(f);
      const o=canvas(416,320);o.getContext('2d').drawImage(previous,i%4*416,Math.floor(i/4)*320,416,320,0,0,416,320);oldFrames.push(o);
      audit.push({phase:i+1,sourceSlot:sourceIndex+1,sourceBounds:part.bounds,outputBounds:[x,y,x+w,y+h],cue:[x+part.cue[0]*sharedScale,y+part.cue[1]*sharedScale],clearance:clearance[i],pixels:part.pixels});
    });
    const bg=(c)=>{const x=c.getContext('2d');x.fillStyle='#e6ecef';x.fillRect(0,0,c.width,c.height);return x;};
    const text=(x,label,px,py,size=17)=>{x.fillStyle='#18303e';x.font=`${size}px sans-serif`;x.fillText(label,px,py);};
    const contact=canvas(1664,1080),cc=bg(contact);
    frames.forEach((f,i)=>{const x=i%4*416,y=Math.floor(i/4)*360;cc.drawImage(f,x,y);cc.strokeStyle='#668997';cc.beginPath();cc.moveTo(x+12,y+296);cc.lineTo(x+404,y+296);cc.stroke();text(cc,`${String(i+1).padStart(2,'0')} ${phases[i]} | gap ${clearance[i]}px`,x+15,y+341);});
    const compare=canvas(1248,640),bc=bg(compare);
    ['CANONICAL P (mirrored)','OLD 12 / fba7fea','REVISED 12'].forEach((s,i)=>text(bc,s,416*i+18,35,21));
    function cropped(im){const cc=canvas(im.width,im.height),x=cc.getContext('2d');x.drawImage(im,0,0);const d=x.getImageData(0,0,cc.width,cc.height).data;let l=cc.width,r=0,t=cc.height,b=0;for(let p=0;p<cc.width*cc.height;p++)if(d[p*4+3]>12){l=Math.min(l,p%cc.width);r=Math.max(r,p%cc.width);t=Math.min(t,Math.floor(p/cc.width));b=Math.max(b,Math.floor(p/cc.width));}const o=canvas(r-l+1,b-t+1);o.getContext('2d').drawImage(cc,l,t,o.width,o.height,0,0,o.width,o.height);return o;}
    [ref,oldFrames[0],frames[0]].map(cropped).forEach((im,i)=>{
      const w=370,h=im.height*w/im.width;bc.save();bc.translate(i*416+(i===0?393:23),370-h);if(i===0)bc.scale(-1,1);bc.drawImage(im,0,0,w,h);bc.restore();
      const silhouette=canvas(im.width,im.height),sx=silhouette.getContext('2d');sx.drawImage(im,0,0);sx.globalCompositeOperation='source-in';sx.fillStyle='#18303e';sx.fillRect(0,0,im.width,im.height);
      bc.save();bc.translate(i*416+(i===0?263:153),452);if(i===0)bc.scale(-1,1);bc.drawImage(silhouette,0,0,110,im.height*110/im.width);bc.restore();
    });text(bc,'Equal full-creature width; aspect preserved. Silhouettes at 110px width.',20,416,17);
    const pairs=canvas(1664,12*350),pc=bg(pairs);
    frames.forEach((f,i)=>{const y=i*350;pc.drawImage(oldFrames[i],180,y);pc.drawImage(f,830,y);text(pc,`${i+1}  ${phases[i]}`,16,y+30);text(pc,'OLD',180,y+340);text(pc,'NEW',830,y+340);pc.strokeStyle='#668997';pc.beginPath();pc.moveTo(150,y+296);pc.lineTo(1280,y+296);pc.stroke();});
    const wrap=canvas(1664,720),wc=bg(wrap);[10,11,0,1].forEach((f,i)=>{wc.drawImage(oldFrames[f],i*416,0);wc.drawImage(frames[f],i*416,360);text(wc,`OLD ${f+1}`,i*416+18,338);text(wc,`NEW ${f+1}`,i*416+18,698);});
    return {sheet:sheet.toDataURL(),contact:contact.toDataURL(),comparison:compare.toDataURL(),pairs:pairs.toDataURL(),wrap:wrap.toDataURL(),frames:frames.map(f=>f.toDataURL()),audit:{sourceSize:[source.width,source.height],sourceOrder,sharedScale,frameSize:[416,320],baseline:296,headCueX:330,clearance,frames:audit}};
  },{raw:url(`${evidence}/generated-source.png`),old:url(`${evidence}/old-12-phase.webp`),canonical:url('public/concept/P.webp'),sourceOrder,clearance,phases});
  const write=(file,data)=>fs.writeFileSync(file,Buffer.from(data.split(',')[1],'base64'));
  write(`${scratch}/candidate.png`,result.sheet);
  await command('magick',[`${scratch}/candidate.png`,'-define','webp:lossless=true',output]);
  for(const [key,name] of [['contact','contact-sheet.png'],['comparison','canonical-old-new.png'],['pairs','old-new-all-phases.png'],['wrap','loop-11-12-1-2.png']])write(`${evidence}/${name}`,result[key]);
  fs.mkdirSync(`${scratch}/frames`,{recursive:true});result.frames.forEach((f,i)=>write(`${scratch}/frames/${String(i).padStart(2,'0')}.png`,f));
  fs.writeFileSync(`${evidence}/packing-audit.json`,JSON.stringify(result.audit,null,2)+'\n');
  console.log(JSON.stringify(result.audit,null,2));
} finally {await browser.close();}

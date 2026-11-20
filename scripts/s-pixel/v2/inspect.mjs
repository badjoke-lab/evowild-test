import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
const dest=path.join(DEMO,'v2/evidence'),report={};
for(const version of ['v1','v2']){
 process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/'+(version==='v2'?'v2/':'');
 const {page,browser,errors}=await openLab({width:1280,height:900});
 try{
  await page.evaluate(()=>{
   sLab.manual(true);const c=sLab.renderer.canvas;c.style.width='512px';c.style.height='320px';
   Object.assign(sLab.state,{method:'stack',mask:true,number:1,idle:true,time:0});
   window.pixelFrame=(settings)=>{
    Object.assign(sLab.state,settings);sLab.draw();
    const gl=sLab.renderer.gl,raw=new Uint8Array(c.width*c.height*4);gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,raw);
    if(gl.getError())throw Error('WebGL readback error');return raw;
   };
   window.readPNG=raw=>{
    const cvs=document.createElement('canvas');cvs.width=c.width;cvs.height=c.height;
    const ctx=cvs.getContext('2d'),im=ctx.createImageData(c.width,c.height);
    for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){
     const i=(y*c.width+x)*4,j=((c.height-1-y)*c.width+x)*4;
     im.data.set(raw.subarray(j,j+3),i);im.data[i+3]=(raw[j]||raw[j+1]||raw[j+2])?255:0;
    }
    ctx.putImageData(im,0,0);return cvs.toDataURL().split(',')[1];
   };
  });
  for(const [name,,,yaw,tilt] of await page.evaluate(()=>sLab.views)){
   const b64=await page.evaluate(([yaw,tilt])=>readPNG(pixelFrame({yaw,tilt})),[yaw,tilt]);
   await fs.writeFile(path.join(dest,version+'-'+name+'.png'),Buffer.from(b64,'base64'));
   if(version==='v2')await fs.writeFile(path.join(DEMO,'v2/assets/views/'+name+'.png'),Buffer.from(b64,'base64'));
  }
  report[version]=await page.evaluate(()=>{
   const c=sLab.renderer.canvas,w=c.width,h=c.height;
   // At low elevation the upper quarter of the silhouette contains the crest.
   // Restrict each triplet to its own common crop at the current camera azimuth.
   let union=0,reversals=0,brightness=0;
   let last,prev,first,second;
   function count(a,b,c){
    let bottom=h,top=0;for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(b[y*w+x]){bottom=Math.min(bottom,y);top=Math.max(top,y);}
    const cut=Math.ceil(top-(top-bottom)*.25);
    for(let j=cut*w;j<(top+1)*w;j++){
     const x=a[j],y=b[j],z=c[j];if(!(x||y||z))continue;union++;
     if((x>12)===(z>12)&&(x>12)!==(y>12))reversals++;
     if((y-x)*(y-z)>0)brightness+=Math.min(Math.abs(y-x),Math.abs(y-z));
    }
   }
   for(let i=0;i<180;i++){
    const raw=pixelFrame({yaw:i*2,tilt:12,idle:true}),v=new Uint8Array(w*h);
    for(let j=0;j<v.length;j++)v[j]=Math.round((raw[j*4]+2*raw[j*4+1]+raw[j*4+2])*.25);
    if(i===0)first=v;if(i===1)second=v;if(i>1)count(prev,last,v);prev=last;last=v;
   }
   count(prev,last,first);count(last,first,second);
   return {samples:180,roi:'upper 25% of silhouette, 12 degrees elevation',coverage_reversal_fraction:reversals/union,mean_luma_reversal_255:brightness/union,union_pixels:union};
  });
  if(version==='v2'){
   report.switchTests=[];
   for(const tilt of [0,12,35,65,90]){
    await page.evaluate(i=>sLab.renderer.sprites.load(i),Math.round(tilt/10));
    const samples=await page.evaluate(tilt=>{
     const out=[];const c=sLab.renderer.canvas;
     for(const desiredSpan of [68,102,126])for(const yaw of [-90,-45,-22,0,45,90,155]){
      const parameters={yaw,tilt,number:1,method:'stack',idle:false,time:.48,course:false,magnification:1};
      pixelFrame(parameters);parameters.magnification=desiredSpan/sLab.renderer.screenSpan;
      const a=pixelFrame(parameters),b=pixelFrame({...parameters,method:'sprite'});
      let intersection=0,union=0,x1=0,y1=0,x2=0,y2=0,n1=0,n2=0,mae=0;
      for(let j=0;j<a.length;j+=4){
       const pa=Math.max(a[j],a[j+1],a[j+2])>12,pb=Math.max(b[j],b[j+1],b[j+2])>12;
       if(!pa&&!pb)continue;union++;intersection+=pa&&pb?1:0;
       const x=(j/4)%c.width,y=Math.floor(j/(4*c.width));
       if(pa){x1+=x;y1+=y;n1++;}if(pb){x2+=x;y2+=y;n2++;}
       mae+=(Math.abs(a[j]-b[j])+Math.abs(a[j+1]-b[j+1])+Math.abs(a[j+2]-b[j+2]))/3;
      }
      out.push({yaw,tilt,desiredSpan,projected_span:sLab.renderer.screenSpan,iou:intersection/union,centroid_delta_px:Math.hypot(x1/n1-x2/n2,y1/n1-y2/n2),rgb_mae_255:mae/union});
     }return out;
    },tilt);report.switchTests.push(...samples);
   }
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.writeFile(path.join(dest,'appearance.json'),JSON.stringify(report,null,2));

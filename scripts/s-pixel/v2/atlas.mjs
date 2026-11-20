// Render the shipped 128-slab meshes. At each texel store paint + face, linear
// surface depth, and four-sample coverage. All 25 poses share a fixed body pivot.
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
const dir=path.join(DEMO,'v2/assets/angles');
await fs.mkdir(dir,{recursive:true});
const {browser,page}=await openLab();
try{
 await page.evaluate(async()=>{
  sLab.manual(true);
  const meta=await fetch('v2/assets/manifest.json').then(r=>r.json());
  const r=sLab.renderer;r.discard(128);
  const worker=new Worker('v2/sections.js');
  await new Promise((resolve,reject)=>{
   let i=0;worker.onerror=reject;worker.onmessage=({data})=>{
    if(data.error){reject(Error(data.error));return;}
    r.add(data);if(++i===meta.poses.length){worker.terminate();resolve();}
    else worker.postMessage({count:128,pose:i});
   };worker.postMessage({count:128,pose:0,meta});
  });
  const gl=r.gl;
  const p=gl.createProgram();
  for(const [type,src] of [[gl.VERTEX_SHADER,`#version 300 es
   precision highp float;layout(location=0) in vec4 grid;uniform vec3 R,U,E,stepSize,origin;
   flat out float tag;out float dist;
   void main(){vec3 v=origin+grid.xyz*stepSize-vec3(0,214,0);
    dist=dot(v,E);gl_Position=vec4(dot(v,R)/476.,dot(v,U)/476.,-dist/512.,1.);tag=grid.w;}`],
   [gl.FRAGMENT_SHADER,`#version 300 es
   precision highp float;flat in float tag;in float dist;out vec4 frag;
   void main(){frag=vec4(tag/255.,clamp(.5+dist/1024.,0.,1.),1.,1.);}`]]){
    const sh=gl.createShader(type);gl.shaderSource(sh,src);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(sh));gl.attachShader(p,sh);
   }
  gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));
  const uni=Object.fromEntries(['R','U','E','stepSize','origin'].map(k=>[k,gl.getUniformLocation(p,k)]));
  const size=112,ss=2,dirs=48,columns=8,tw=size*ss,w=columns*tw,h=dirs/columns*tw;
  r.canvas.width=w;r.canvas.height=h;
  gl.useProgram(p);gl.uniform3f(uni.stepSize,meta.sx,meta.height/128,meta.sz);gl.uniform3f(uni.origin,meta.x0-385,0,meta.z0);
  gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.disable(gl.BLEND);gl.disable(gl.DITHER);gl.clearColor(0,0,0,0);
  const pixels=new Uint8Array(w*h*4);
  window.bakeElevation=degrees=>{
   const tiles=[];
   const e=degrees*Math.PI/180;
   for(let pose=0;pose<meta.poses.length;pose++){
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);const m=r.mesh.get('128/'+pose);gl.bindVertexArray(m.vao);
    for(let k=0;k<dirs;k++){
     const a=k*Math.PI*2/dirs;
     gl.viewport(k%columns*tw,Math.floor(k/columns)*tw,tw,tw);
     gl.uniform3f(uni.R,Math.cos(a),0,-Math.sin(a));gl.uniform3f(uni.U,-Math.sin(a)*Math.sin(e),Math.cos(e),-Math.cos(a)*Math.sin(e));gl.uniform3f(uni.E,Math.sin(a)*Math.cos(e),Math.sin(e),Math.cos(a)*Math.cos(e));
     gl.drawElements(gl.TRIANGLES,m.len,gl.UNSIGNED_INT,0);
    }
    gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
    for(let k=0;k<dirs;k++){
     const l=k%columns*tw,b=Math.floor(k/columns)*tw;
     const raster=new Uint8Array(size*size*3);
     let x0=size,y0=size,x1=0,y1=0;
     for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const i=((b+y*2)*w+l+x*2)*4;
      let n=0,sum=0,tag=0,closest=-1;
      for(const j of [i,i+4,i+w*4,i+w*4+4]){
       if(!pixels[j])continue;
       n++;sum+=pixels[j+1];if(pixels[j+1]>closest){closest=pixels[j+1];tag=pixels[j];}
      }
      if(!n)continue;
      const dest=(y*size+x)*3;raster[dest]=tag;raster[dest+1]=Math.round(sum/n);raster[dest+2]=Math.round(n*255/4);
      x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
     }
     const width=x1-x0+1,height=y1-y0+1,bytes=new Uint8Array(width*height*3);
     for(let j=0;j<height;j++)bytes.set(raster.subarray(((j+y0)*size+x0)*3,((j+y0)*size+x1+1)*3),j*width*3);
     tiles.push({id:pose*dirs+k,w:width,h:height,x:x0,y:y0,bytes});
    }
   }
   const rects=[],pages=[];let u=0,v=0,line=0,pageId=0;
   tiles.sort((a,b)=>b.h-a.h);
   for(const t of tiles){
    if(u+t.w+2>2048){v+=line;u=0;line=0;}
    if(v+t.h+2>2048){pageId++;u=v=line=0;}
    t.u=u+1;t.v=v+1;t.page=pageId;u+=t.w+2;line=Math.max(line,t.h+2);
    rects[t.id]=[pageId,t.u,t.v,t.w,t.h,t.x,t.y];
   }
   for(let k=0;k<=pageId;k++){
    const items=tiles.filter(t=>t.page===k);const bw=Math.max(...items.map(t=>t.u+t.w+1)),bh=Math.max(...items.map(t=>t.v+t.h+1));
    const c=document.createElement('canvas');c.width=bw;c.height=bh;const ctx=c.getContext('2d'),im=ctx.createImageData(bw,bh);
    for(let i=3;i<im.data.length;i+=4)im.data[i]=255;
    for(const t of items)for(let y=0;y<t.h;y++)for(let x=0;x<t.w;x++){
     const j=((t.v+y)*bw+t.u+x)*4,i=(y*t.w+x)*3;
     im.data[j]=t.bytes[i];im.data[j+1]=t.bytes[i+1];im.data[j+2]=t.bytes[i+2];
    }
    ctx.putImageData(im,0,0);pages.push({w:bw,h:bh,png:c.toDataURL().split(',')[1]});
   }
   return {rects,pages};
  };
 });
 const meta={size:112,unit:8.5,directions:48,angles:[]};
 for(let elev=0;elev<=90;elev+=10){
  const {rects,pages}=await page.evaluate(e=>bakeElevation(e),elev);
  const files=[];
  for(const [i,p] of pages.entries()){
   const file='e'+elev+'-'+i+'.png';await fs.writeFile(path.join(dir,file),Buffer.from(p.png,'base64'));files.push([file,p.w,p.h]);
  }
  meta.angles.push({elev,files,rects});console.log('baked',elev,files);
 }
 await fs.writeFile(path.join(dir,'index.json'),JSON.stringify(meta));
}finally{await browser.close();}

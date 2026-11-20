// Registered colour/coverage/depth sprites from the 128-layer model.
import {FarSprites} from './far-sprites.js';
import {program,common} from '../renderer.js';

export const threshold=`
float threshold(){
 ivec2 p=ivec2(gl_FragCoord.xy)&3;
 int x=p.x,y=p.y;
 return (float((((x&1)^(y&1))*8+(y&1)*4+((x>>1)^(y>>1))*2+(y>>1)))+.5)/16.;
}`;
const vs=`#version 300 es
precision highp float;
layout(location=1)in vec4 placement; // x, z, local view azimuth, source azimuth
layout(location=2)in vec4 rect;
layout(location=3)in vec4 tile; // x/y offset, sprite fraction, planted feet bits
${common}
uniform vec2 uElev,uSourceElev;
out vec3 q;out vec2 origin,plane;flat out vec2 ray,footDir;flat out vec3 eyeLocal;
flat out vec4 uvRect;flat out vec4 info;flat out float centreDepth;
void main(){
 vec2 corner=vec2((gl_VertexID==1||gl_VertexID==2||gl_VertexID==4)?1.:0.,(gl_VertexID==2||gl_VertexID==4||gl_VertexID==5)?1.:0.);
 vec2 screenPos=(tile.xy-56.+mix(vec2(-6.),rect.zw+6.,corner))*8.5;
 vec3 centre=vec3(placement.x,214.,placement.y);
 gl_Position=project(centre+screenPos.x*uRight+screenPos.y*uUp);
 uvRect=rect;info=tile;centreDepth=dot(centre-uTarget,uEye);
 float s=sin(placement.z),c=cos(placement.z),sb=sin(placement.w),cb=cos(placement.w);
 vec3 right=vec3(c,0.,-s),up=vec3(-s*uElev.x,uElev.y,-c*uElev.x),eye=vec3(s*uElev.y,uElev.x,c*uElev.y);
 vec3 rb=vec3(cb,0.,-sb),ub=vec3(-sb*uSourceElev.x,uSourceElev.y,-cb*uSourceElev.x),eb=vec3(sb*uSourceElev.y,uSourceElev.x,cb*uSourceElev.y);
 q=right*screenPos.x+up*screenPos.y;
 origin=vec2(dot(q,rb),dot(q,ub))/8.5+56.-info.xy;
 ray=vec2(dot(eye,rb),dot(eye,ub))/8.5;
 eyeLocal=eye;plane=vec2(dot(q,eb),1./dot(eye,eb));footDir=vec2(rb.x,ub.x)/8.5;

}`;
const fs=`#version 300 es
precision highp float;precision highp int;
uniform sampler2D uAtlas,uDepth;
uniform float uDrift;
in vec3 q;in vec2 origin,plane;flat in vec2 ray,footDir;flat in vec3 eyeLocal;flat in vec4 uvRect;flat in vec4 info;flat in float centreDepth;
out vec4 frag;
${threshold}
void main(){
 if(info.z>=0. && info.z<1. && threshold()>=info.z)discard;
 if(info.z<0. && threshold()<-info.z)discard;
 float d=0.;
 for(int j=0;j<2;j++){
   vec2 at=clamp(origin+ray*d,vec2(.01),uvRect.zw-.01);
   float depth=(texelFetch(uDepth,ivec2(uvRect.xy+at),0).r-.5)*1024.;
   d=(depth-plane.x)*plane.y;
 }
 vec3 body=q+eyeLocal*d;
 int foot=(body.x<35.?0:2)+(body.z>0.?0:1);
 float move=((int(info.w+.5)&(1<<foot))!=0)?uDrift*(1.-smoothstep(54.,170.,214.+body.y)):0.;
 vec2 at=origin+ray*d-footDir*move;
 if(any(lessThan(at,vec2(-.5)))||any(greaterThan(at,uvRect.zw+.5)))discard;
 vec4 col=texture(uAtlas,(uvRect.xy+at)/vec2(textureSize(uAtlas,0)));
 if(col.a<.13)discard;
 frag=col;
 gl_FragDepth=.5-(centreDepth+d+move*eyeLocal.x)/48000.;
}`;
export class Impostors{
 constructor(gl,index){
  this.gl=gl;this.index=index;
  this.pass=program(gl,vs,fs);this.banks=new Map();this.bytes=0;
  this.vao=gl.createVertexArray();this.buffer=gl.createBuffer();gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
  for(let i=1;i<=3;i++){gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,4,gl.FLOAT,false,48,(i-1)*16);gl.vertexAttribDivisor(i,1);}
  gl.bindVertexArray(null);this.far=new FarSprites(gl,this.buffer);
 }
 async load(i){
  if(this.banks.has(i))return this.banks.get(i).promise;
  const gl=this.gl,bank={pages:[],ready:false};this.banks.set(i,bank);
  bank.promise=(async()=>{
   for(const [file,w,h,depthFile] of this.index.angles[i].files){
    const decode=async(name,alpha)=>{
     const response=await fetch(new URL('./assets/angles/'+name,import.meta.url));
     if(!response.ok)throw Error(name+' '+response.status);
     return createImageBitmap(await response.blob(),{colorSpaceConversion:'none',premultiplyAlpha:alpha});
    };
    const [paint,depth]=await Promise.all([decode(file,'premultiply'),decode(depthFile,'none')]);
    const upload=(internal,format,image,filter)=>{
     const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);
     gl.texImage2D(gl.TEXTURE_2D,0,internal,format,gl.UNSIGNED_BYTE,image);image.close();
     gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,filter);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,filter);
     gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
     return tex;
    };
    const tex=upload(gl.RGBA8,gl.RGBA,paint,gl.LINEAR),z=upload(gl.R8,gl.RED,depth,gl.NEAREST);
    bank.pages.push({tex,z,bytes:w*h*5});this.bytes+=w*h*5;
   }
   bank.ready=true;
  })().catch(e=>{this.release(i);throw e;});
  return bank.promise;
 }
 release(i){
  const bank=this.banks.get(i);if(!bank)return;
  for(const p of bank.pages){this.gl.deleteTexture(p.tex);this.gl.deleteTexture(p.z);this.bytes-=p.bytes;}this.banks.delete(i);
 }
 select(elevation,onReady){
  const i=Math.max(0,Math.min(9,Math.round(elevation/10)));
  this.wanted=i;
  if(this.failed===i)return -1;
  if(!this.banks.has(i))this.load(i).then(onReady).catch(e=>{this.failed=i;onReady(e);});
  for(const [j,b] of this.banks)if(Math.abs(i-j)>1&&b.ready)this.release(j);
  const bank=this.banks.get(i);if(bank?.ready)return i;
  const adjacent=[i-1,i+1].find(j=>this.banks.get(j)?.ready);
  return adjacent??-1;
 }
 draw(grouped,far,bank,use,elev,drift){
  const gl=this.gl,{u}=this.pass;
  use(this.pass);gl.uniform1i(u.uDepth,1);gl.uniform1i(u.uAtlas,0);gl.uniform1f(u.uDrift,drift);
  const ang=this.index.angles[bank].elev*Math.PI/180;
  gl.uniform2f(u.uSourceElev,Math.sin(ang),Math.cos(ang));gl.uniform2f(u.uElev,Math.sin(elev),Math.cos(elev));
  gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.activeTexture(gl.TEXTURE0);
  gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
  for(const [page,data] of grouped){
   const image=this.banks.get(bank).pages[page];
   gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,image.z);
   gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,image.tex);
   gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STREAM_DRAW);gl.drawArraysInstanced(gl.TRIANGLES,0,6,data.length/12);
  }
  for(const [page,data] of far)this.far.draw(data,this.banks.get(bank).pages[page],[Math.sin(ang),Math.cos(ang)],drift,this.buffer,use);
  gl.disable(gl.BLEND);gl.bindVertexArray(null);
 }
}

import {common,program} from '../renderer.js';
import {threshold} from '../v2/impostors.js';
import {PaintedSurface,bytes} from '../v3/surface.js';

const vertex = `#version 300 es
precision highp float;
layout(location=0) in vec4 gridPose;
layout(location=1) in vec4 placement;
layout(location=2) in vec2 instanceInfo;
layout(location=3) in vec2 detail;
uniform vec3 origin,stepSize; uniform ivec3 paintOrigin,paintSize; uniform float quantization,drift;
${common}
out vec3 paintCell; flat out float cover,shade;
void main(){
 vec3 grid=gridPose.xyz/quantization;
 int pose=int(gridPose.w);
 paintCell=grid.xzy-vec3(paintOrigin.zyx)+vec3((pose%5)*paintSize.z,(pose/5)*paintSize.y,0);
 cover=instanceInfo.y;
 shade=.75+detail.x/800.;
 vec3 p=origin+grid*stepSize;
 p.x+=drift*detail.y/255.;
 vec2 dir=placement.zw;
 vec2 world=vec2(dir.x*p.x-dir.y*p.z,dir.y*p.x+dir.x*p.z)+placement.xy;
 gl_Position=project(vec3(world.x,p.y,world.y));
}`;
function fragment(fade) {
 return `#version 300 es
 precision highp float;precision highp int;precision highp sampler2DArray;
 in vec3 paintCell;flat in float cover,shade;
 uniform sampler2DArray paint;uniform vec3 palette[18];
 out vec4 color;
 ${fade?threshold:''}
 void main(){
  ${fade?'if(cover<1. && threshold()<1.-cover)discard;':''}
  ivec3 at=ivec3(floor(paintCell));
  at.z=clamp(at.z,0,127);
  int ink=int(texelFetch(paint,at,0).r*255.+.5);
  color=vec4(palette[ink]*shade,1.);
 }`;
}
export class RaceSurface extends PaintedSurface {
 static geometry = new URL('./assets/geometry.gz',import.meta.url);
 static index = new URL('./assets/index.json',import.meta.url);
 static vertex = vertex;
 static fragment = fragment(true);

 async load(){
  const [,buffer]=await Promise.all([super.load(),bytes(new URL('./assets/detail.gz',import.meta.url))]);
  if(buffer.byteLength!==this.info.vertexBytes/4)throw Error('表面属性と頂点数が一致しません');
  const gl=this.gl;
  gl.bindVertexArray(this.vao);
  gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER,new Uint8Array(buffer),gl.STATIC_DRAW);
  gl.enableVertexAttribArray(3);gl.vertexAttribPointer(3,2,gl.UNSIGNED_BYTE,false,2,0);
  gl.bindVertexArray(null);
  this.fade=this.pass;
  this.opaque=program(gl,vertex,fragment(false));this.configure(this.opaque);
  this.bytes+=buffer.byteLength;
 }
 draw(batches,use,drift){
  const full=new Map(),partial=new Map();
  for(const [key,batch] of batches){
   let opaque=true;
   for(let i=5;i<batch.places.length;i+=6)if(batch.places[i]<1){opaque=false;break;}
   (opaque?full:partial).set(key,batch);
  }
  // Only transition batches need screen-door coverage. The opaque shader can
  // use early depth rejection without running a discard-capable fragment.
  this.pass=this.opaque;
  const triangles=super.draw(full,use,drift);
  this.pass=this.fade;
  return triangles+super.draw(partial,use,drift);
 }
}

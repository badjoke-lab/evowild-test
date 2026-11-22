import {FacingIndices} from './visible.js';
import {common,program} from '../renderer.js';
import {threshold} from '../v2/impostors.js';

export async function bytes(url){
 const response=await fetch(url);
 if(!response.ok)throw Error(`${response.status} ${url}`);
 const buffer=await response.arrayBuffer(), magic=new Uint8Array(buffer,0,2);
 return magic[0]===31&&magic[1]===139 ? new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer() : buffer;
}

const vertex=`#version 300 es
precision highp float;
layout(location=0) in vec4 gridPose;
layout(location=1) in vec4 placement;
layout(location=2) in vec2 instanceInfo;
uniform vec3 origin,stepSize;uniform float quantization,drift;
${common}
out highp vec3 grid;flat out int pose;flat out float cover;
void main(){
 grid=gridPose.xyz/quantization;pose=int(gridPose.w);cover=instanceInfo.y;
 vec3 p=origin+grid*stepSize;
 int foot=(p.x<35.?0:2)+(p.z>0.?0:1);
 if((int(instanceInfo.x)&(1<<foot))!=0)p.x+=drift*(1.-smoothstep(54.,170.,p.y));
 vec2 dir=placement.zw;
 vec2 world=vec2(dir.x*p.x-dir.y*p.z,dir.y*p.x+dir.x*p.z)+placement.xy;
 gl_Position=project(vec3(world.x,p.y,world.y));
}`;
const fragment=`#version 300 es
precision highp float;precision highp int;precision highp sampler2DArray;
in vec3 grid;flat in int pose;flat in float cover;
uniform sampler2DArray paint;uniform ivec3 paintOrigin,paintSize;uniform vec3 palette[18],stepSize;
out vec4 color;
${threshold}
void main(){
 if(cover<1. && threshold()<1.-cover)discard;
 ivec3 cell=clamp(ivec3(floor(grid.yzx))-paintOrigin,ivec3(0),paintSize-1);
 ivec3 at=ivec3(cell.z+(pose%5)*paintSize.z,cell.y+(pose/5)*paintSize.y,cell.x);
 int ink=int(texelFetch(paint,at,0).r*255.+.5);
 vec3 n=normalize(cross(dFdx(grid*stepSize),dFdy(grid*stepSize)));
 vec3 weights=abs(n);float shade=dot(weights,vec3(n.x>0.?.89:.95,n.y>0.?1.04:.78,n.z>0.?1.:.88))/max(.0001,weights.x+weights.y+weights.z);
 color=vec4(palette[ink]*shade,1.);
}`;

export class PaintedSurface{
 constructor(gl,meta){this.gl=gl;this.meta=meta;this.pass=program(gl,vertex,fragment);this.bytes=0;}
 async load(){
  const url=f=>new URL('./assets/runtime/'+f,import.meta.url);
  const [info,geo,paint]=await Promise.all([fetch(url('index.json')).then(r=>r.json()),bytes(url('geometry.gz')),bytes(url('paint.gz'))]);
  this.info=info;const gl=this.gl;
  this.vao=gl.createVertexArray();gl.bindVertexArray(this.vao);
  this.vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.vb);gl.bufferData(gl.ARRAY_BUFFER,new Uint8Array(geo,0,info.vertexBytes),gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,4,gl.UNSIGNED_SHORT,false,8,0);
  this.ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,this.ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint32Array(geo,info.vertexBytes),gl.STATIC_DRAW);
  this.instances=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.instances);this.scratch=new Float32Array(100*6);
  gl.bufferData(gl.ARRAY_BUFFER,this.scratch.byteLength,gl.DYNAMIC_DRAW);
  for(const attr of [1,2]){gl.enableVertexAttribArray(attr);gl.vertexAttribDivisor(attr,1);}
  gl.bindVertexArray(null);
  const [sy,sz,sx]=info.paintSizeYZX,section=sy*sz*sx;
  if(paint.byteLength!==section*info.poses.length)throw Error('ボクセル色配列の長さが一致しません');
  this.paint=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D_ARRAY,this.paint);
  gl.texStorage3D(gl.TEXTURE_2D_ARRAY,1,gl.R8,sx*5,sz*5,sy);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);
  for(let i=0;i<info.poses.length;i++)gl.texSubImage3D(gl.TEXTURE_2D_ARRAY,0,(i%5)*sx,Math.floor(i/5)*sz,0,sx,sz,sy,gl.RED,gl.UNSIGNED_BYTE,new Uint8Array(paint,i*section,section));
  for(const key of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D_ARRAY,key,gl.NEAREST);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT,4);
  const {p,u}=this.pass;gl.useProgram(p);gl.uniform1i(u.paint,2);
  gl.uniform3iv(u.paintSize,info.paintSizeYZX);gl.uniform3iv(u.paintOrigin,info.paintOriginYZX);
  gl.uniform1f(u.quantization,info.quantization);gl.uniform3f(u.origin,this.meta.x0-385,0,this.meta.z0);
  gl.uniform3f(u.stepSize,this.meta.sx,this.meta.height/128,this.meta.sz);
  gl.uniform3fv(u.palette,Float32Array.from(this.meta.palette.flatMap(c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16)/255))));
  this.bytes=geo.byteLength+paint.byteLength+this.scratch.byteLength;
  this.facing=new FacingIndices(gl,geo,info,this.meta);
 }
 draw(batches,use,drift){
  if(!batches.size)return 0;
  const gl=this.gl;use(this.pass);gl.uniform1f(this.pass.u.drift,drift);gl.activeTexture(gl.TEXTURE2);gl.bindTexture(gl.TEXTURE_2D_ARRAY,this.paint);
  gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.instances);
  let floatOffset=0,tris=0;
  for(const batch of batches.values()){this.scratch.set(batch.places,floatOffset);batch.offset=floatOffset*4;floatOffset+=batch.places.length;}
  gl.bufferSubData(gl.ARRAY_BUFFER,0,this.scratch,0,floatOffset);
  for(const {pose,level,places,offset,direction} of batches.values()){
   const mesh=this.info.poses[pose][level];
   gl.vertexAttribPointer(1,4,gl.FLOAT,false,24,offset);gl.vertexAttribPointer(2,2,gl.FLOAT,false,24,offset+16);
   const slice=direction==null?null:this.facing.get(mesh,direction);
   const count=slice?slice.count:mesh.count;
   gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,slice?slice.ib:this.ib);
   gl.drawElementsInstanced(gl.TRIANGLES,count,gl.UNSIGNED_INT,slice?0:mesh.first*4,places.length/6);
   tris+=count/3*places.length/6;
  }
  gl.activeTexture(gl.TEXTURE0);gl.bindVertexArray(null);return tris;
 }
}

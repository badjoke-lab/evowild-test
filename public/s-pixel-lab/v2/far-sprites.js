// A depth sprite is sampled on a regular 6×6 grid. Its backing pixels still
// come from one of the 48 painted views; the grid adjusts parallax, contact
// compensation and inter-runner depth before rasterization.
import {common,program} from '../renderer.js';
const vs=`#version 300 es
precision highp float;
layout(location=0)in vec2 unitUV;
layout(location=1)in vec4 placement;
layout(location=2)in vec4 rect;
layout(location=3)in vec4 tile;
uniform highp sampler2D depthImage;uniform vec2 srcElev;uniform float drift;
${common}
out vec2 uv;flat out float fraction;
void main(){
 vec2 texel=mix(vec2(-.75),rect.zw+.75,unitUV);
 vec2 baked=(texel+tile.xy-56.)*8.5;
 float d=(texelFetch(depthImage,ivec2(rect.xy+clamp(texel,vec2(.01),rect.zw-.01)),0).r-.5)*1024.;
 float s=sin(placement.w),c=cos(placement.w);
 vec3 rb=vec3(c,0.,-s),ub=vec3(-s*srcElev.x,srcElev.y,-c*srcElev.x),eb=vec3(s*srcElev.y,srcElev.x,c*srcElev.y);
 vec3 p=rb*baked.x+ub*baked.y+eb*d+vec3(0.,214.,0.);
 int foot=(p.x<35.?0:2)+(p.z>0.?0:1);
 if((int(tile.w+.5)&(1<<foot))!=0)p.x+=drift*(1.-smoothstep(54.,170.,p.y));
 // placement.z is local yaw, related to the camera's horizontal basis.
 float a=cos(placement.z),b=sin(placement.z);
 float ca=uRight.x*a-uRight.z*b,sa=uRight.x*b+uRight.z*a;
 vec2 world=vec2(ca*p.x-sa*p.z,sa*p.x+ca*p.z)+placement.xy;
 gl_Position=project(vec3(world.x,p.y,world.y));uv=(rect.xy+texel)/vec2(textureSize(depthImage,0));fraction=tile.z;
}`;
const fs=`#version 300 es
precision mediump float;
uniform sampler2D image;
in highp vec2 uv;flat in highp float fraction;out vec4 frag;
void main(){
 if(fraction<1.){
  ivec2 p=ivec2(gl_FragCoord.xy)&3;int x=p.x,y=p.y;
  float t=(float(((x&1)^(y&1))*8+(y&1)*4+((x>>1)^(y>>1))*2+(y>>1))+.5)/16.;
  if(t>=fraction)discard;
 }
 vec4 p=texture(image,uv);if(p.a<.13)discard;frag=p;}`;
export class FarSprites{
 constructor(gl,instanceBuffer){
  this.gl=gl;this.pass=program(gl,vs,fs);this.vao=gl.createVertexArray();
  gl.bindVertexArray(this.vao);const vertices=[],indices=[],n=6;
  for(let y=0;y<=n;y++)for(let x=0;x<=n;x++)vertices.push(x/n,y/n);
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){
   const a=y*(n+1)+x;indices.push(a,a+1,a+n+2,a,a+n+2,a+n+1);
  }
  this.elements=indices.length;
  gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indices),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,instanceBuffer);
  for(let i=1;i<=3;i++){gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,4,gl.FLOAT,false,48,(i-1)*16);gl.vertexAttribDivisor(i,1);}
  gl.bindVertexArray(null);this.geometryBytes=vertices.length*4+indices.length*2;
 }
 draw(data,page,srcElev,drift,buffer,use){
  const gl=this.gl,{u}=this.pass;use(this.pass);gl.uniform2fv(u.srcElev,srcElev);gl.uniform1f(u.drift,drift);
  gl.uniform1i(u.image,0);gl.uniform1i(u.depthImage,1);
  gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,page.z);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,page.tex);
  gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STREAM_DRAW);
  gl.disable(gl.CULL_FACE);gl.drawElementsInstanced(gl.TRIANGLES,this.elements,gl.UNSIGNED_SHORT,0,data.length/12);gl.enable(gl.CULL_FACE);
 }
}

import {common,program} from '../renderer.js';
// The racetrack is fixed in world space. Mipmaps keep its markings stable as
// the camera moves and avoid evaluating signed-distance and line AA per pixel.
const vs=`#version 300 es
${common}
out vec2 ground;out vec2 relative;
void main(){
 vec2 ndc=vec2((gl_VertexID<<1)&2,gl_VertexID&2)*2.-1.;
 vec3 p=uTarget+uRight*ndc.x*uExtent.x+uUp*ndc.y*uExtent.y;
 ground=p.xz-uEye.xz*(p.y/max(.0001,uEye.y));relative=(ground-uTarget.xz)/uExtent.y;
 gl_Position=vec4(ndc,.999,1.);
}`;
const fs=`#version 300 es
precision highp float;uniform sampler2D plan;in vec2 ground,relative;out vec4 color;
void main(){
 vec3 sky=vec3(.825,.863,.849), base=vec3(.871,.902,.882);
 vec3 paint=texture(plan,ground/vec2(9600.,6400.)+.5).rgb;
 float fog=1./(1.+length(relative)*.20);
 vec2 g=ground/80.;vec2 grid=abs(fract(g-.5)-.5)/max(fwidth(g),vec2(.001));
 float fine=1.-smoothstep(.15,1.1,min(grid.x,grid.y));
 // Sampled track carries lane and finish colours, the open field carries grid.
 float fieldMask=smoothstep(.013,.033,length(paint-base));
 color=vec4(mix(sky,mix(base-.06*fine,paint,fieldMask),fog),1.);
}`;
export class TrackFloor{
 constructor(gl){this.gl=gl;this.pass=program(gl,vs,fs);this.vao=gl.createVertexArray();}
 init(){
  const gl=this.gl,c=document.createElement('canvas');c.width=1920;c.height=1280;
  const ctx=c.getContext('2d');ctx.fillStyle='#dee6e1';ctx.fillRect(0,0,c.width,c.height);
  ctx.translate(c.width/2,c.height/2);ctx.scale(.2,.2);
  const oval=(radius,color,width)=>{
   ctx.beginPath();ctx.moveTo(-1900,-radius);ctx.lineTo(1900,-radius);
   ctx.arc(1900,0,radius,-Math.PI/2,Math.PI/2);ctx.lineTo(-1900,radius);
   ctx.arc(-1900,0,radius,Math.PI/2,Math.PI*1.5);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
  };
  oval(1750,'#b1bfb8',1110);for(let r=1195;r<=2305;r+=110)oval(r,'#ebede4',4.5);
  ctx.fillStyle='#cc8a69';ctx.fillRect(-12,1195,24,1110);
  this.texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.texture);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,this.preparePlan?.(c) || c);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  for(const key of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,key,gl.CLAMP_TO_EDGE);
  gl.generateMipmap(gl.TEXTURE_2D);this.bytes=Math.round(c.width*c.height*4*4/3);
 }
 draw(frame,use){
  const gl=this.gl;gl.activeTexture(gl.TEXTURE0);if(!this.texture)this.init();
  gl.bindTexture(gl.TEXTURE_2D,this.texture);use(this.pass);gl.uniform1i(this.pass.u.plan,0);
  gl.disable(gl.DEPTH_TEST);gl.bindVertexArray(this.vao);gl.drawArrays(gl.TRIANGLES,0,3);
 }
}

import {TrackFloor} from '../v3/track.js';
import {common,program} from '../renderer.js';

// The mip level is constant across an orthographic ground plane. Fog is smooth
// at the scale of these screen tiles; the lane/grid texture stays full-size.
const vertex = `#version 300 es
${common}
uniform vec2 viewport;
out vec2 ground; flat out float mip; out float fog;
void main(){
 int cell=gl_VertexID/6, corner=gl_VertexID%6;
 vec2 uv=(vec2(cell%12,cell/12)+vec2(corner==1||corner==2||corner==4?1.:0.,corner==2||corner==4||corner==5?1.:0.))/vec2(12.,8.);
 vec2 ndc=uv*2.-1.;
 vec2 slope=uEye.xz/max(.0001,uEye.y);
 vec2 dx=(uRight.xz-slope*uRight.y)*uExtent.x;
 vec2 dy=(uUp.xz-slope*uUp.y)*uExtent.y;
 ground=uTarget.xz-uTarget.y*slope+ndc.x*dx+ndc.y*dy;
 mip=log2(max(length(dx)/viewport.x,length(dy)/viewport.y)*.4);
 fog=1./(1.+length((ground-uTarget.xz)/uExtent.y)*.20);
 gl_Position=vec4(ndc,.999,1.);
}`;
const fragment = `#version 300 es
precision highp float;
uniform sampler2D plan;
in vec2 ground; flat in float mip; in float fog; out vec4 color;
void main(){
 vec2 uv=ground/vec2(9600.,6400.)+.5;
 // The empty margin contains the same 80-unit grid as the infield. Continue
 // that grid to the horizon without tiling the race markings.
 if(any(greaterThan(abs(uv-.5),vec2(.5))))uv=(vec2(160.)+mod(ground,80.))/vec2(9600.,6400.);
 color=vec4(mix(vec3(.825,.863,.849),textureLod(plan,uv,mip).rgb,fog),1.);
}`;

export class RaceFloor extends TrackFloor {
 constructor(gl) {
  super(gl);
  gl.deleteProgram(this.pass.p);
  this.pass=program(gl,vertex,fragment);
 }
 preparePlan(canvas) {
  const image=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height);
  const pixels=image.data;
  // Sixteen texture pixels span one 80-unit grid cell. Only the field carries
  // this grid. Keep the original finish paint, lanes and antialiased strokes.
  for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++){
   const i=(y*image.width+x)*4;
   const field=Math.max(0,1-Math.max(Math.abs(pixels[i]-222),Math.abs(pixels[i+1]-230),Math.abs(pixels[i+2]-225))/8);
   const edge=Math.min((x%16)+.5,15.5-x%16,(y%16)+.5,15.5-y%16);
   const tone=15*field*Math.max(0,1-edge/1.6);
   for(let c=0;c<3;c++)pixels[i+c]-=tone;
  }
  return image;
 }
 draw({w,h},use) {
  const gl=this.gl;
  gl.activeTexture(gl.TEXTURE0);
  if(!this.texture)this.init();
  gl.bindTexture(gl.TEXTURE_2D,this.texture);
  use(this.pass);gl.uniform1i(this.pass.u.plan,0);gl.uniform2f(this.pass.u.viewport,w,h);
  gl.disable(gl.DEPTH_TEST);
  gl.bindVertexArray(this.vao);
  gl.drawArrays(gl.TRIANGLES,0,12*8*6);
 }
}

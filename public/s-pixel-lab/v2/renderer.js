import {SectionsRenderer,runnerVS,runnerFS,program} from '../renderer.js';
import {Impostors,threshold} from './impostors.js';
const vs=runnerVS.replace('out vec3 vColor;', 'layout(location=2) in float spriteFraction; flat out float fraction; out vec3 vColor;').replace(' vec3 p=uOrigin',' fraction=spriteFraction; vec3 p=uOrigin');
const fs=runnerFS.replace('in vec3 vColor;',threshold+'\nflat in float fraction; in vec3 vColor;').replace('color=vec4','if(fraction>0. && threshold()<fraction)discard;color=vec4');
export class CrowdRenderer extends SectionsRenderer{
 constructor(canvas,meta,atlas,onReady){
  super(canvas,meta,[vs,fs]);this.sprites=new Impostors(this.gl,atlas);this.onReady=onReady;this.coverage=new CoverageBuffer(this.gl);
  this.fades=new Map();this.fadeBuffer=this.gl.createBuffer();this.mix={near:0,transition:0,sprite:0};
 }
 beginFrame(s,ext,w,h){
  const nearPossible=700*h/(2*ext)*1.25>110;
  if(s.coverage!==false && s.method!=='sprite' && (s.method==='stack'||nearPossible))this.coverage.begin(w,h);
 }
 endFrame(){this.coverage.finish();}
 drawFloor(s,frame,use){
  const gl=this.gl,{aim,ext,w,h}=frame;
  // Only the floor is cached. Roots, shadows, depth and every gait pose still
  // render on each frame. The cache key describes the full floor projection.
  // During orbit/tracking the projection normally changes every frame.
  const key=[s.course,s.yaw,s.tilt,aim[0],aim[1],aim[2],ext,w,h].join('/');
  if(s.course||s.spin){super.drawFloor(s,frame,use);return;}
  if(this.floorKey!==key){
   if(!this.floorTexture){
    this.floorTexture=gl.createTexture();
    this.floorCopy=program(gl,`#version 300 es
    void main(){vec2 v=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(v*2.-1.,0.,1.);}`,
    `#version 300 es
    precision mediump float;uniform sampler2D image;out vec4 color;
    void main(){color=texelFetch(image,ivec2(gl_FragCoord.xy),0);}`);
    this.floorFbo=gl.createFramebuffer();
   }
   gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.floorTexture);
   if(w!==this.floorW||h!==this.floorH){
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    this.floorW=w;this.floorH=h;
   }
   gl.bindFramebuffer(gl.FRAMEBUFFER,this.floorFbo);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,this.floorTexture,0);
   super.drawFloor(s,frame,use);this.floorKey=key;
   gl.bindFramebuffer(gl.FRAMEBUFFER,this.coverage.active?this.coverage.fb:null);
  }
  gl.disable(gl.DEPTH_TEST);
  if(this.coverage.active){
   gl.useProgram(this.floorCopy.p);gl.uniform1i(this.floorCopy.u.image,0);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.floorTexture);
   gl.bindVertexArray(this.blank);gl.drawArrays(gl.TRIANGLES,0,3);
  }else{
   gl.bindFramebuffer(gl.READ_FRAMEBUFFER,this.floorFbo);
   gl.blitFramebuffer(0,0,w,h,0,0,w,h,gl.COLOR_BUFFER_BIT,gl.NEAREST);
   gl.bindFramebuffer(gl.READ_FRAMEBUFFER,null);
  }
 }
 get atlasBytes(){return this.sprites.bytes;}
 bindFade(pose){
  const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,this.fadeBuffer);
  gl.bufferData(gl.ARRAY_BUFFER,Float32Array.from(this.fades.get(pose)),gl.STREAM_DRAW);
  gl.enableVertexAttribArray(2);gl.vertexAttribPointer(2,1,gl.FLOAT,false,0,0);gl.vertexAttribDivisor(2,1);
 }
 drawActors(s,frame,use){
  const {aim,eye,ext,h}=frame,near=new Map(),cards=new Map(),far=new Map();this.fades.clear();
  const mix={near:0,transition:0,sprite:0,spriteBlend:0,offscreen:0};
  const angularSize=700*h/(2*ext),cameraDistance=ext/Math.tan(Math.PI/8);
  const useSprite=s.method!=='stack'&&(angularSize*.80<142||s.method==='sprite');
  const bank=useSprite?this.sprites.select(s.tilt,this.onReady):-1;
  const atlas=this.sprites.index,tilt=s.tilt*Math.PI/180,yaw=s.yaw*Math.PI/180;
  for(const [pose,places] of frame.groups){
   const feet=this.meta.poses[pose].feet;
   const planted=['nearF','farF','nearH','farH'].reduce((bits,k,i)=>bits|(Number(feet[k].contact)<<i),0);
   for(let i=0;i<places.length;i+=4){
    const [x,z,a,b]=places.slice(i,i+4);
    if(s.course && s.magnification>1){
     // The original camera already fits everyone at 1×. After an explicit
     // zoom, reject only bounds wholly outside the orthographic viewport.
     const outside=(axis,limit)=>{
      const [ax,ay,az]=axis;
      const centre=(x-aim[0])*ax+(224-aim[1])*ay+(z-aim[2])*az;
      const radius=Math.abs(a*ax+b*az)*450+Math.abs(ay)*240+Math.abs(-b*ax+a*az)*110;
      return Math.abs(centre)>limit+radius;
     };
     if(outside(frame.right,ext*frame.w/h)||outside(frame.up,ext)){mix.offscreen++;continue;}
    }
    const depth=(x-aim[0])*eye[0]+(214-aim[1])*eye[1]+(z-aim[2])*eye[2];
    const ratio=Math.max(.80,Math.min(1.25,cameraDistance/Math.max(50,cameraDistance-depth)));
    const size=angularSize*ratio;
    let fraction=bank<0?0:s.method==='sprite'?1:Math.max(0,Math.min(1,(142-size)/32));
    fraction=fraction*fraction*(3-2*fraction);
    if(fraction<1){
     if(!near.has(pose)){near.set(pose,[]);this.fades.set(pose,[]);}
     near.get(pose).push(x,z,a,b);this.fades.get(pose).push(fraction);
    }
    if(fraction>0){
     const angle=yaw+Math.atan2(b,a),n=atlas.directions;
     const k=(Math.round(angle*n/(2*Math.PI))%n+n)%n;
     const [pg,u,v,w,h,dx,dy]=atlas.angles[bank].rects[pose*n+k];
     const farWeight=s.fastSprites===false?0:Math.max(0,Math.min(1,(110-size)/16));
     const append=(batch,weight)=>{
      if(!batch.has(pg))batch.set(pg,[]);
      batch.get(pg).push(x,z,angle,k*Math.PI*2/n,u,v,w,h,dx,dy,weight,planted);
     };
     if(farWeight<1)append(cards,farWeight>0?-farWeight:fraction);
     if(farWeight>0)append(far,farWeight);
     if(farWeight>0&&farWeight<1)mix.spriteBlend++;
    }
    if(fraction===0)mix.near++;else if(fraction===1)mix.sprite++;else mix.transition++;
   }
  }
  const tris=super.drawActors(s,{groups:near},use);
  if(cards.size||far.size){
   const tick=s.time/this.meta.period*s.samples;
   const drift=s.course&&!s.idle?(tick-Math.floor(tick+1e-6))*this.meta.stride/s.samples:0;
   this.sprites.draw(cards,far,bank,use,tilt,drift);
  }
  this.mix=mix;this.screenSpan=angularSize;this.bank=bank;
  return tris+2*(mix.sprite+mix.transition+mix.spriteBlend)+[...far.values()].reduce((sum,data)=>sum+data.length/12*(this.sprites.far.elements/3-2),0);
 }
}

/** Multisample coverage for the thin, close-range crest. The sprite bake already
 * contains four coverage samples per texel. Resolve to the original canvas size. */
class CoverageBuffer{
 constructor(gl){this.gl=gl;this.samples=Math.min(4,gl.getParameter(gl.MAX_SAMPLES));}
 begin(w,h){
  const gl=this.gl;if(this.samples<2)return;
  if(w!==this.w||h!==this.h){
   this.release();this.w=w;this.h=h;this.fb=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,this.fb);
   const attach=(format,at)=>{
    const rb=gl.createRenderbuffer();gl.bindRenderbuffer(gl.RENDERBUFFER,rb);
    gl.renderbufferStorageMultisample(gl.RENDERBUFFER,this.samples,format,w,h);
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER,at,gl.RENDERBUFFER,rb);return rb;
   };
   this.color=attach(gl.RGB8,gl.COLOR_ATTACHMENT0);this.depth=attach(gl.DEPTH_COMPONENT16,gl.DEPTH_ATTACHMENT);
   if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE){this.release();this.samples=0;return;}
  }
  gl.bindFramebuffer(gl.FRAMEBUFFER,this.fb);this.active=true;
 }
 finish(){
  if(!this.active)return;
  const gl=this.gl;gl.bindFramebuffer(gl.READ_FRAMEBUFFER,this.fb);gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,null);
  gl.blitFramebuffer(0,0,this.w,this.h,0,0,this.w,this.h,gl.COLOR_BUFFER_BIT,gl.NEAREST);
  gl.bindFramebuffer(gl.FRAMEBUFFER,null);this.active=false;
 }
 release(){
  const gl=this.gl;gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  if(this.fb){gl.deleteRenderbuffer(this.color);gl.deleteRenderbuffer(this.depth);gl.deleteFramebuffer(this.fb);}
  this.fb=null;this.w=this.h=0;
 }
 get bytes(){return this.fb?this.w*this.h*this.samples*6:0;}
}

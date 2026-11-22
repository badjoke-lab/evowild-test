// Each nonempty brick gets its projected bounding rectangle. The fragment
// shader intersects the original indexed cells and writes the real hit depth.
import {common, program} from '../renderer.js';

const vs = `#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
layout(location=1) in vec4 placement;
layout(location=2) in vec3 poseData; // first brick, count, contact bits
uniform usampler2D uBoxes;
uniform vec3 uOrigin, uStep;
uniform float uDrift;
${common}
out vec3 pPlane;
flat out vec3 ray;
flat out ivec4 tile;
flat out float centreDepth;
uvec4 boxTexel(int i){ return texelFetch(uBoxes,ivec2(i&1023,i>>10),0); }
vec3 toGrid(vec3 localWorld, float slope){
  vec3 g=localWorld/uStep;
  g.x-=g.y*slope;
  return g;
}
vec3 local(vec3 world){
  vec2 a=placement.zw;
  return vec3(a.x*world.x+a.y*world.z,world.y,-a.y*world.x+a.x*world.z);
}
void main(){
  int i=gl_VertexID/6;
  if(i>=int(poseData.y)){
    gl_Position=vec4(2.,2.,2.,1.);return;
  }
  int address=2*(int(poseData.x)+i);
  uvec4 box=boxTexel(address);
  vec3 size=vec3(boxTexel(address+1).xyz);
  tile=ivec4(size,int(box.w));
  vec3 lower=uOrigin+vec3(box.xyz)*uStep, halfSpan=size*.5*uStep;
  vec3 centre=lower+halfSpan;
  int foot=(centre.x<35.?0:2)+(centre.z>0.?0:1);
  float drift=(int(poseData.z)&(1<<foot))!=0?uDrift:0.;
  float shift0=drift*(1.-smoothstep(54.,170.,lower.y));
  float shift1=drift*(1.-smoothstep(54.,170.,lower.y+2.*halfSpan.y));
  float halfShift=(shift1-shift0)*.5;
  float slope=(shift1-shift0)/(size.y*uStep.x);
  centre.x+=(shift0+shift1)*.5;
  vec3 right=local(uRight), up=local(uUp);
  vec2 xz=vec2(placement.z*centre.x-placement.w*centre.z,
               placement.w*centre.x+placement.z*centre.z)+placement.xy;
  vec3 world=vec3(xz.x,centre.y,xz.y);
  vec2 space=vec2(abs(right.x*halfSpan.x)+abs(right.y*halfSpan.y+right.x*halfShift)+abs(right.z*halfSpan.z),
                  abs(up.x*halfSpan.x)+abs(up.y*halfSpan.y+up.x*halfShift)+abs(up.z*halfSpan.z));
  const vec2 corners[6]=vec2[6](vec2(-1,-1),vec2(1,-1),vec2(1,1),vec2(-1,-1),vec2(1,1),vec2(-1,1));
  vec2 off=space*corners[gl_VertexID%6];
  vec4 clip=project(world);
  gl_Position=vec4(clip.xy+off/uExtent,clip.z,1.);
  pPlane=size*.5+toGrid(right*off.x+up*off.y,slope);
  ray=toGrid(local(-uEye),slope);
  centreDepth=dot(world-uTarget,uEye);
}`;

const fs = `#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
uniform usampler2D uCells;
uniform vec3 uPalette[18];
in vec3 pPlane;
flat in vec3 ray;
flat in ivec4 tile;
flat in float centreDepth;
out vec4 color;
void main(){
  // Preserve the sign of tiny components while keeping exact axial views finite.
  vec3 choose=mix(vec3(-1.),vec3(1.),greaterThanEqual(ray,vec3(0.)));
  vec3 inv=choose/max(abs(ray),vec3(1.e-8));
  vec3 lower=(vec3(0.)-pPlane)*inv, upper=(vec3(tile.xyz)-pPlane)*inv;
  vec3 entry=min(lower,upper), leave=max(lower,upper);
  float t=max(max(entry.x,entry.y),entry.z);
  float end=min(min(leave.x,leave.y),leave.z);
  if(end<=t)discard;
  int axis=entry.x>=entry.y && entry.x>=entry.z ? 0 : entry.y>=entry.z ? 1 : 2;
  ivec3 direction=ivec3(choose);
  ivec3 cell=clamp(ivec3(floor(pPlane+ray*(t+.0002))),ivec3(0),tile.xyz-1);
  ivec3 nextPlane=cell+max(direction,ivec3(0));
  vec3 next=(vec3(nextPlane)-pPlane)*inv;
  vec3 delta=abs(inv);
  const vec3 negativeShade=vec3(.95,.78,.88);
  const vec3 positiveShade=vec3(.89,1.04,1.);
  for(int n=0;n<39;n++){
    int address=tile.w+(cell.y*tile.z+cell.z)*tile.x+cell.x;
    uint paint=texelFetch(uCells,ivec2(address&2047,address>>11),0).r;
    if(paint!=0u){
      float shade=direction[axis]>0?negativeShade[axis]:positiveShade[axis];
      color=vec4(uPalette[int(paint)]*shade,1.);
      gl_FragDepth=.5-(centreDepth-t)/48000.;
      return;
    }
    axis=next.x<=next.y && next.x<=next.z ? 0 : next.y<=next.z ? 1 : 2;
    t=next[axis];
    cell[axis]+=direction[axis];
    if(t>=end || cell[axis]<0 || cell[axis]>=tile[axis])discard;
    next[axis]+=delta[axis];
  }
  discard;
}`;

const base=new URL('./assets/exact/',import.meta.url);
async function fetchAsset(file){
  const response=await fetch(new URL(file,base));
  if(!response.ok)throw Error(file+' '+response.status);
  return response;
}
async function unpack(file){
  const response=await fetchAsset(file);
  const stream=response.body.pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).arrayBuffer();
}

export class ExactSurface {
  constructor(gl,meta){
    this.gl=gl;this.meta=meta;this.bytes=0;
    this.pass=program(gl,vs,fs);
    this.palette=Float32Array.from(meta.palette.flatMap(c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16)/255)));
    this.vao=gl.createVertexArray();
    gl.bindVertexArray(this.vao);
    this.buffer=gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
    this.capacity=0;
    for(const [location,length,offset] of [[1,4,0],[2,3,16]]){
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(location,length,gl.FLOAT,false,28,offset);
      gl.vertexAttribDivisor(location,1);
    }
    gl.bindVertexArray(null);
  }

  load(){
    if(!this.ready)this.ready=this.upload().catch(error=>{this.ready=null;throw error;});
    return this.ready;
  }

  async upload(){
    const [index,boxes,cells]=await Promise.all([
      fetchAsset('index.json').then(r=>r.json()),unpack('bricks.u32.gz'),unpack('paint.u8.gz')
    ]);
    if(boxes.byteLength!==index.descriptors*32 || cells.byteLength!==index.paintBytes)
      throw Error('Invalid voxel brick asset lengths');
    const gl=this.gl;
    const texture=(data,width,channels,format,external,type)=>{
      const height=Math.ceil(data.length/(width*channels));
      if(height>gl.getParameter(gl.MAX_TEXTURE_SIZE))throw Error('Voxel brick texture exceeds WebGL limit');
      const padded=new data.constructor(width*height*channels);padded.set(data);
      const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D,0,format,width,height,0,external,type,padded);
      this.bytes+=padded.byteLength;
      return tex;
    };
    this.boxes=texture(new Uint32Array(boxes),1024,4,gl.RGBA32UI,gl.RGBA_INTEGER,gl.UNSIGNED_INT);
    this.cells=texture(new Uint8Array(cells),2048,1,gl.R8UI,gl.RED_INTEGER,gl.UNSIGNED_BYTE);
    this.index=index;
    this.feet=this.meta.poses.map(({feet})=>['nearF','farF','nearH','farH']
      .reduce((mask,k,i)=>mask|(Number(feet[k].contact)<<i),0));
  }

  draw(groups,use,drift){
    if(!groups.size || !this.index)return 0;
    let count=0,maxBricks=0;
    for(const [pose,places] of groups){
      count+=places.length/4;
      maxBricks=Math.max(maxBricks,this.index.poses[pose].count);
    }
    const gl=this.gl;
    gl.bindVertexArray(this.vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
    if(count>this.capacity){
      const capacity=Math.max(count,Math.max(8,this.capacity*2));
      this.staging=new Float32Array(capacity*7);
      gl.bufferData(gl.ARRAY_BUFFER,this.staging.byteLength,gl.DYNAMIC_DRAW);
      this.bytes+=(capacity-this.capacity)*28;
      this.capacity=capacity;
    }
    let at=0;
    for(const [pose,places] of groups){
      const {first,count}=this.index.poses[pose];
      for(let i=0;i<places.length;i+=4){
        this.staging[at++]=places[i];this.staging[at++]=places[i+1];
        this.staging[at++]=places[i+2];this.staging[at++]=places[i+3];
        this.staging[at++]=first;this.staging[at++]=count;this.staging[at++]=this.feet[pose];
      }
    }
    gl.bufferSubData(gl.ARRAY_BUFFER,0,this.staging,0,at);
    const {u}=this.pass;
    use(this.pass);
    gl.uniform3fv(u.uOrigin,this.index.origin);
    gl.uniform3fv(u.uStep,this.index.step);
    gl.uniform3fv(u.uPalette,this.palette);
    gl.uniform1f(u.uDrift,drift);
    gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.boxes);gl.uniform1i(u.uBoxes,0);
    gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,this.cells);gl.uniform1i(u.uCells,1);
    gl.drawArraysInstanced(gl.TRIANGLES,0,maxBricks*6,count);
    gl.bindVertexArray(null);gl.activeTexture(gl.TEXTURE0);
    return 2*maxBricks*count;
  }
}

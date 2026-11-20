const common=`
uniform vec3 uRight,uUp,uEye,uTarget;
uniform vec2 uExtent;
vec4 project(vec3 world){
  vec3 p=world-uTarget;
  return vec4(dot(p,uRight)/uExtent.x,dot(p,uUp)/uExtent.y,-dot(p,uEye)/24000.,1.);
}
`;
const runnerVS=`#version 300 es
precision highp float;
layout(location=0) in vec4 grid;
layout(location=1) in vec4 placement;
uniform vec3 uStep,uOrigin;
uniform vec4 uFootDrift;
uniform vec3 uPalette[18];
${common}
out vec3 vColor;
void main(){
 vec3 p=uOrigin+grid.xyz*uStep;
 // Compensate continuous root travel between the two sampled support poses.
 // Coordinates identify each lower limb below the carpus/hock.
 float drift=p.x<35.?(p.z>0.?uFootDrift.x:uFootDrift.y):(p.z>0.?uFootDrift.z:uFootDrift.w);
 p.x+=drift*(1.-smoothstep(54.,170.,p.y));
 vec2 a=placement.zw;
 vec2 xz=vec2(a.x*p.x-a.y*p.z,a.y*p.x+a.x*p.z)+placement.xy;
 gl_Position=project(vec3(xz.x,p.y,xz.y));
 int tag=int(grid.w+.5);
 int face=tag%8;
 float shade=face==3?1.04:face==2?.78:face==4?.88:face==0?.95:face==1?.89:1.;
 vColor=uPalette[tag/8]*shade;
}`;
const runnerFS=`#version 300 es
precision mediump float;
in vec3 vColor;out vec4 color;void main(){color=vec4(vColor,1.);}`;
const floorVS=`#version 300 es
precision highp float;
out vec2 uv;
void main(){uv=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2))*2.-1.;gl_Position=vec4(uv,.999,1.);}`;
const floorFS=`#version 300 es
precision highp float;
in vec2 uv;out vec4 color;
${common}
uniform int uCourse;
float line(float x){return 1.-smoothstep(.25,1.22,abs(x)/max(fwidth(x),.28));}
void main(){
 vec3 sky=vec3(.825,.863,.849);
 vec3 p=uTarget+uRight*uv.x*uExtent.x+uUp*uv.y*uExtent.y;
 vec2 ground=p.xz-uEye.xz*p.y/max(.0001,uEye.y);
 float dist=length(ground-uTarget.xz);
 float fog=exp(-dist/(uExtent.y*5.));
 vec2 grid=ground/80.;
 vec2 d=abs(fract(grid-.5)-.5)/max(fwidth(grid),vec2(.001));
 float fine=1.-smoothstep(.15,1.1,min(d.x,d.y));
 vec3 base=mix(sky,vec3(.871,.902,.882),fog);
 base-=vec3(.065,.058,.04)*fine*fog;
 if(uCourse==0){
   float radius=length(ground);
   base=mix(base,vec3(.56,.63,.59),.45*line(radius-420.)*fog);
   base=mix(base,vec3(.57,.64,.60),.30*line(radius-434.)*fog);
 } else {
   float lane=length(vec2(max(abs(ground.x)-1900.,0.),ground.y))-1750.;
   float track=1.-smoothstep(555.,565.,abs(lane));
   base=mix(base,vec3(.68,.735,.72),track*fog*.82);
   float marks=line(mod(lane+554.,110.)-55.);
   base=mix(base,vec3(.96,.963,.91),marks*track*fog*.9);
   float finish=1.-smoothstep(0.,3.,abs(ground.x)-12.);
   if(ground.y>0.)base=mix(base,vec3(.94,.42,.21),finish*track*fog);
 }
 color=vec4(base,1.);
}`;
const shadowVS=`#version 300 es
precision highp float;
layout(location=1) in vec4 placement;
${common}
out vec2 uv;
void main(){
 uv=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2))*2.-1.;
 vec2 q=uv*vec2(320.,52.)+vec2(20.,0.);
 vec2 a=placement.zw;vec2 xz=vec2(a.x*q.x-a.y*q.y,a.y*q.x+a.x*q.y)+placement.xy;
 gl_Position=project(vec3(xz.x,.1,xz.y));
}`;
const shadowFS=`#version 300 es
precision mediump float;
in vec2 uv;out vec4 color;
void main(){float r=dot(uv,uv);if(r>=1.)discard;color=vec4(.13,.20,.21,.18*(1.-smoothstep(.08,1.,r)));}`;
function program(gl,vs,fs){
  const p=gl.createProgram();
  for(const [type,source] of [[gl.VERTEX_SHADER,vs],[gl.FRAGMENT_SHADER,fs]]){
    const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);
    if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));
    gl.attachShader(p,s);gl.deleteShader(s);
  }
  gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));
  const u={};for(let i=0;i<gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS);i++){
    const n=gl.getActiveUniform(p,i).name;u[n.replace('[0]','')]=gl.getUniformLocation(p,n);
  }
  return {p,u};
}
export const courseLength=7600+2*Math.PI*1750;
export function course(distance,lane=0){
 const R=1750+lane, bend=Math.PI*R, perimeter=7600+2*bend;
 let s=((distance%perimeter)+perimeter)%perimeter;
 if(s<3800)return [1900-s,R,1,0];
 s-=3800;
 if(s<bend){const a=s/R;return [-1900-R*Math.sin(a),R*Math.cos(a),Math.cos(a),Math.sin(a)];}
 s-=bend;
 if(s<3800)return [-1900+s,-R,-1,0];
 const a=(s-3800)/R;return [1900+R*Math.sin(a),-R*Math.cos(a),-Math.cos(a),-Math.sin(a)];
}
export class SectionsRenderer{
 constructor(canvas,meta,actorShaders=[runnerVS,runnerFS]){
   this.canvas=canvas;this.meta=meta;
   const gl=canvas.getContext('webgl2',{alpha:false,antialias:false,preserveDrawingBuffer:true});
   if(!gl) throw Error('WebGL 2 を利用できません。ブラウザのハードウェアアクセラレーションを確認してください。');
   this.gl=gl;this.mesh=new Map();
   this.runner=program(gl,...actorShaders);this.floor=program(gl,floorVS,floorFS);
   this.shadow=program(gl,shadowVS,shadowFS);
   this.palette=Float32Array.from(meta.palette.flatMap(v=>[1,3,5].map(i=>parseInt(v.slice(i,i+2),16)/255)));
   this.instance=gl.createBuffer();this.blank=gl.createVertexArray();
   this.shadowVAO=gl.createVertexArray();gl.bindVertexArray(this.shadowVAO);this.placements();gl.bindVertexArray(null);
   gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);
 }
 placements(){
   const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,this.instance);
   gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,4,gl.FLOAT,false,0,0);gl.vertexAttribDivisor(1,1);
 }
 add({pose,count,verts,elements}){
   const gl=this.gl,vao=gl.createVertexArray();gl.bindVertexArray(vao);
   const vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,verts,gl.STATIC_DRAW);
   gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,4,gl.UNSIGNED_SHORT,false,0,0);
   const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,elements,gl.STATIC_DRAW);
   this.placements();gl.bindVertexArray(null);
   this.mesh.set(count+'/'+pose,{vao,vb,ib,len:elements.length});
 }
 discard(count){
   const gl=this.gl;
   for(const [k,m] of this.mesh)if(k.startsWith(count+'/')){
     gl.deleteBuffer(m.vb);gl.deleteBuffer(m.ib);gl.deleteVertexArray(m.vao);this.mesh.delete(k);
   }
 }
 draw(s){
   const {gl,canvas:c,meta}=this;
   const w=Math.max(1,Math.round(c.clientWidth*Math.min(devicePixelRatio,1.5))), h=Math.max(1,Math.round(c.clientHeight*Math.min(devicePixelRatio,1.5)));
   if(w!==c.width||h!==c.height){c.width=w;c.height=h;}
   gl.viewport(0,0,w,h);
   const yaw=s.yaw*Math.PI/180, tilt=s.tilt*Math.PI/180;
   const eye=[Math.sin(yaw)*Math.cos(tilt),Math.sin(tilt),Math.cos(yaw)*Math.cos(tilt)];
   const right=[Math.cos(yaw),0,-Math.sin(yaw)], up=[-Math.sin(yaw)*Math.sin(tilt),Math.cos(tilt),-Math.cos(yaw)*Math.sin(tilt)];
   const cols=Math.ceil(Math.sqrt(s.number)), rows=Math.ceil(s.number/cols);
   const movers=[],groups=new Map();
   const length=s.time*meta.stride/meta.period+3690;
   let target=s.course?course(length):[0,0];
   for(let i=0;i<s.number;i++){
     let place;
     if(s.course){
       const lane=(i%Math.min(cols,10)-(Math.min(cols,10)-1)/2)*103;
       // Lane path length differs in the bend. Lead runner sets the common pace.
       place=course(length-Math.floor(i/cols)*760,lane);
     }else{
       place=[((i%cols)-(cols-1)/2)*810,(Math.floor(i/cols)-(rows-1)/2)*445,1,0];
     }
     let f=(Math.floor(s.time/meta.period*s.samples+1e-6)+i*7)%s.samples;
     const pose=s.idle?0:1+f*(meta.frames/s.samples);
     if(!groups.has(pose))groups.set(pose,[]);
     groups.get(pose).push(...place);movers.push(...place);
   }
   let ext=Math.max(293,420*h/w);
   if(s.number>1)ext=Math.max(445, (cols*810*.53+rows*445*.24)*h/w,rows*230+210);
   if(s.course&&s.number===1)ext*=1.36;
   if(s.course&&s.number>1){target=course(length-(rows-1)*380);ext=Math.max(ext,rows*475);}
   ext*=s.zoom||1;
   const aim=[target[0],s.number===1?214:105,target[1]];
   // A near-vertical overhead view can put the entire nose-to-tail length on
   // the short screen axis. Fit all oriented specimen bounds, including bends.
   for(let i=0;i<movers.length;i+=4){
     const [x,z,a,b]=movers.slice(i,i+4);
     const dx=x-aim[0],dz=z-aim[2],dy=224-aim[1];
     function extentOn(basis){
       const [bx,by,bz]=basis;
       return Math.abs(dx*bx+dy*by+dz*bz)+Math.abs(a*bx+b*bz)*370+
         Math.abs(by)*224+Math.abs(-b*bx+a*bz)*65;
     }
     ext=Math.max(ext,extentOn(up)*1.025,extentOn(right)*h/w*1.025);
   }
   ext/=s.magnification||1;
   function use(pass){
     const {p,u}=pass;gl.useProgram(p);
     gl.uniform3fv(u.uEye,eye);gl.uniform3fv(u.uRight,right);gl.uniform3fv(u.uUp,up);gl.uniform3fv(u.uTarget,aim);gl.uniform2f(u.uExtent,ext*w/h,ext);
   }
   this.beginFrame?.(s,ext,w,h);
   gl.clear(gl.DEPTH_BUFFER_BIT);gl.disable(gl.CULL_FACE);
   if(s.mask){gl.clearColor(0,0,0,1);gl.clear(gl.COLOR_BUFFER_BIT);}
   else{
     this.drawFloor(s,{aim,ext,w,h},use);
     use(this.shadow);gl.bindVertexArray(this.shadowVAO);gl.bindBuffer(gl.ARRAY_BUFFER,this.instance);
     gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(movers),gl.STREAM_DRAW);
     gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
     gl.drawArraysInstanced(gl.TRIANGLES,0,3,s.number);gl.disable(gl.BLEND);
   }
   gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);
   const triangles=this.drawActors(s,{groups,aim,eye,up,right,ext,w,h},use);
   this.endFrame?.();return triangles;
 }
 drawFloor(s,frame,use){
   const gl=this.gl;
   use(this.floor);gl.uniform1i(this.floor.u.uCourse,s.course?1:0);gl.bindVertexArray(this.blank);
   gl.disable(gl.DEPTH_TEST);gl.drawArrays(gl.TRIANGLES,0,3);
 }
 drawActors(s,{groups},use){
   const {gl,meta}=this;
   use(this.runner);const {u}=this.runner;
   gl.uniform3f(u.uOrigin,meta.x0-385,0,meta.z0);gl.uniform3f(u.uStep,meta.sx,meta.height/s.layers,meta.sz);
   gl.uniform3fv(u.uPalette,this.palette);
   let tris=0;
   for(const [pose,places] of groups){
     const m=this.mesh.get(s.layers+'/'+pose);if(!m)continue;
     const tick=s.time/meta.period*s.samples;
     const drift=s.course&&!s.idle?(tick-Math.floor(tick+1e-6))*meta.stride/s.samples:0;
     const feet=meta.poses[pose].feet;
     gl.uniform4fv(u.uFootDrift,['nearF','farF','nearH','farH'].map(k=>feet[k].contact?drift:0));
     gl.bindVertexArray(m.vao);this.bindFade?.(pose);gl.bindBuffer(gl.ARRAY_BUFFER,this.instance);
     gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(places),gl.STREAM_DRAW);
     gl.drawElementsInstanced(gl.TRIANGLES,m.len,gl.UNSIGNED_INT,0,places.length/4);
     tris+=m.len/3*places.length/4;
   }
   gl.bindVertexArray(null);return tris;
 }
}

export {common,program,runnerVS,runnerFS};

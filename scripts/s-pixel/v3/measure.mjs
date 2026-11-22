// Paired camera/gait trajectories with one synchronous GPU readback every frame.
import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
import {DEMO} from '../browser.mjs';
import {RACES,raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';

const version=process.argv[2];
if(!['v2','v3'].includes(version))throw Error('Pass v2 or v3');
const profiles={desktop:{mobile:false,width:877,height:414,viewport:{width:1280,height:900},cpu:1},mobile:{mobile:true,width:352,height:335,viewport:{width:390,height:844},cpu:4}};
const filter=process.env.MEASURE_PROFILE,scenarioFilter=process.env.MEASURE_RACE;
const method=process.env.MEASURE_METHOD||'lod',samples=Number(process.env.MEASURE_FRAMES||48);
const destination=process.env.MEASURE_OUT||path.join(DEMO,'v3/evidence',version+'-race.json');
if(!Number.isInteger(samples)||samples<2||!['lod','surface','stack','sprite','exact'].includes(method))throw Error('Invalid measurement configuration');
if(filter && !(filter in profiles) || scenarioFilter && !(scenarioFilter in RACES))throw Error('Unknown selected scenario or profile');
const url=(process.env.LAB_BASE_URL||'http://127.0.0.1:4173/s-pixel-lab/')+version+'/';

// Observe logical allocation sizes at their WebGL entry points. Record the
// drawing context's live buffers only; image decode via an auxiliary canvas
// and the browser-owned default framebuffer are deliberately outside this sum.
function instrument(){
 const proto=WebGL2RenderingContext.prototype;
 const contexts=new WeakMap();
 function state(gl){
  if(!contexts.has(gl))contexts.set(gl,{buffers:new Set(),textures:new Map(),renderbuffers:new Map(),calls:0,triangles:0,blits:0,unknownFormats:new Set()});
  return contexts.get(gl);
 }
 window.sLabMeter=state;
 function wrap(name,fn){const old=proto[name];proto[name]=function(...args){const result=old.apply(this,args);fn(this,state(this),args,result);return result;};}
 wrap('createBuffer',(_g,s,_a,b)=>s.buffers.add(b));wrap('deleteBuffer',(_g,s,[b])=>s.buffers.delete(b));
 wrap('deleteTexture',(_g,s,[t])=>s.textures.delete(t));wrap('deleteRenderbuffer',(_g,s,[r])=>s.renderbuffers.delete(r));
 function texBytes(gl,format,s){
  const formats=new Map([[gl.RED,1],[gl.R8,1],[gl.R8UI,1],[gl.RG,2],[gl.RG8,2],[gl.RG8UI,2],[gl.RGB,3],[gl.RGB8,3],[gl.RGBA,4],[gl.RGBA8,4],[gl.RGBA8UI,4],[gl.R16F,2],[gl.RGBA16F,8],[gl.R32F,4],[gl.RGBA32F,16],[gl.RGBA32UI,16],[gl.RGB32UI,12],[gl.RG32UI,8],[gl.R32UI,4],[gl.DEPTH_COMPONENT16,2],[gl.DEPTH_COMPONENT24,3],[gl.DEPTH24_STENCIL8,4]]);
  if(!formats.has(format)){s.unknownFormats.add(format);return 0;}return formats.get(format);
 }
 function boundTexture(gl,target){
  const binding=target===gl.TEXTURE_2D?gl.TEXTURE_BINDING_2D:target===gl.TEXTURE_3D?gl.TEXTURE_BINDING_3D:gl.TEXTURE_BINDING_2D_ARRAY;
  return gl.getParameter(binding);
 }
 function texture(gl,s,target,mip,format,w,h,d=1){
  const tex=boundTexture(gl,target);if(!tex)return;
  if(!s.textures.has(tex))s.textures.set(tex,new Map());
  s.textures.get(tex).set(mip,{format,w,h,d,bytes:w*h*d*texBytes(gl,format,s)});
 }
 wrap('texImage2D',(g,s,a)=>{
  const fromImage=a.length===6;
  texture(g,s,a[0],a[1],a[2],fromImage?a[5].width:a[3],fromImage?a[5].height:a[4]);
 });
 wrap('texImage3D',(g,s,a)=>texture(g,s,a[0],a[1],a[2],a[3],a[4],a[5]));
 for(const call of ['texStorage2D','texStorage3D'])wrap(call,(g,s,[target,mips,format,w,h,d=1])=>{
  for(let i=0;i<mips;i++)texture(g,s,target,i,format,Math.max(1,w>>i),Math.max(1,h>>i),target===g.TEXTURE_3D?Math.max(1,d>>i):d);
 });
 wrap('generateMipmap',(g,s,[target])=>{
  const levels=s.textures.get(boundTexture(g,target)),base=levels?.get(0);
  if(!base)return;
  const {w,h,d,format}=base;const levelsUsed=Math.floor(Math.log2(Math.max(w,h,target===g.TEXTURE_3D?d:1)));
  for(let i=1;i<=levelsUsed;i++)texture(g,s,target,i,format,Math.max(1,w>>i),Math.max(1,h>>i),target===g.TEXTURE_3D?Math.max(1,d>>i):d);
 });
 wrap('renderbufferStorageMultisample',(g,s,[,samples,format,w,h])=>s.renderbuffers.set(g.getParameter(g.RENDERBUFFER_BINDING),samples*w*h*texBytes(g,format,s)));
 wrap('renderbufferStorage',(g,s,[,format,w,h])=>s.renderbuffers.set(g.getParameter(g.RENDERBUFFER_BINDING),w*h*texBytes(g,format,s)));
 for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){
  const arrays=name.includes('Arrays'),instanced=name.includes('Instanced');
  wrap(name,(g,s,args)=>{
   const [mode]=args,n=args[arrays?2:1],instances=instanced?args[arrays?3:4]:1;
   s.calls++;s.triangles+=instances*(mode===g.TRIANGLES?n/3:mode===g.TRIANGLE_STRIP||mode===g.TRIANGLE_FAN?Math.max(0,n-2):0);
  });
 }
 wrap('blitFramebuffer',(_g,s)=>s.blits++);
}

async function memory(browser,page,cdp){
 const resources=await page.evaluate(()=>{
  const g=sLab.renderer.gl,s=sLabMeter(g),binding=g.getParameter(g.COPY_READ_BUFFER_BINDING);
  let buffer=0;
  for(const b of s.buffers){g.bindBuffer(g.COPY_READ_BUFFER,b);buffer+=g.getBufferParameter(g.COPY_READ_BUFFER,g.BUFFER_SIZE);}
  g.bindBuffer(g.COPY_READ_BUFFER,binding);
  const sum=a=>a.reduce((p,q)=>p+q,0);
  if(g.getError()!==g.NO_ERROR)throw Error('Invalid WebGL buffer memory query');
  return {buffer_bytes:buffer,texture_bytes:sum([...s.textures.values()].map(m=>sum([...m.values()].map(level=>level.bytes)))),renderbuffer_bytes:sum([...s.renderbuffers.values()]),unknown_formats:[...s.unknownFormats]};
 });
 if(resources.unknown_formats.length)throw Error('Uncounted texture format '+resources.unknown_formats);
 const heap=await cdp.send('Runtime.getHeapUsage');
 const session=await browser.newBrowserCDPSession();const {processInfo}=await session.send('SystemInfo.getProcessInfo');await session.detach();
 let rss=0;const byType={};
 for(const proc of processInfo){
  try{const status=await fs.readFile('/proc/'+proc.id+'/status','utf8'),kb=Number(/^VmRSS:\s+(\d+)/m.exec(status)?.[1]||0);rss+=kb;byType[proc.type]=(byType[proc.type]||0)+kb;}
  catch(e){if(e.code!=='ENOENT'&&e.code!=='EACCES')throw e;}
 }
 return {...resources,gl_mib:(resources.buffer_bytes+resources.texture_bytes+resources.renderbuffer_bytes)/1048576,js_heap_mib:heap.usedSize/1048576,rss_mib:rss?rss/1024:null,rss_kib_by_type:byType};
}

async function measure(page,states){
 return page.evaluate(async (states)=>{
  const s=sLab.state,r=sLab.renderer,g=r.gl,m=sLabMeter(g),timer=g.getExtension('EXT_disjoint_timer_query_webgl2');
  const queries=[],frames=[],geometries=[];const pixel=new Uint8Array(4),raf=()=>new Promise(requestAnimationFrame);
  const original=r.drawActors;
  let latest;r.drawActors=function(state,frame,use){latest=frame;return original.call(this,state,frame,use);};
  const draw=(frame,timed)=>{
   Object.assign(s,frame);m.calls=0;m.triangles=0;m.blits=0;
   let query;if(timed && timer){query=g.createQuery();g.beginQuery(timer.TIME_ELAPSED_EXT,query);}
   const start=performance.now();sLab.draw();const submit=performance.now();
   if(query){g.endQuery(timer.TIME_ELAPSED_EXT);queries.push(query);}
   g.readPixels(r.canvas.width>>1,r.canvas.height>>1,1,1,g.RGBA,g.UNSIGNED_BYTE,pixel);
   const end=performance.now();
   if(timed){frames.push({submit_ms:submit-start,sync_ms:end-start,calls:m.calls,triangles:m.triangles,blits:m.blits,mix:{...r.mix},camera:{time:s.time,yaw:s.yaw,tilt:s.tilt,magnification:s.magnification}});geometries.push(latest);}
   return end;
  };
  try{
   for(const f of states.slice(0,3)){await raf();draw(f,false);}
   let previous=performance.now();
   for(const frame of states){await raf();const end=draw(frame,true);frames.at(-1).interval_ms=end-previous;previous=end;}
   if(queries.length){
    for(let k=0;k<60 && !g.getQueryParameter(queries.at(-1),g.QUERY_RESULT_AVAILABLE);k++)await raf();
    const disjoint=g.getParameter(timer.GPU_DISJOINT_EXT);
    queries.forEach((q,i)=>{frames[i].gpu_ms=(!disjoint&&g.getQueryParameter(q,g.QUERY_RESULT_AVAILABLE))?g.getQueryParameter(q,g.QUERY_RESULT)/1e6:null;});
   }
   // Conservative oriented bounds are the same as v2's visibility test. Centre
   // count and full-body count distinguish a clipped edge from a wholly visible
   // actor. Audit after the timed frames, outside GPU/CPU/RAF interval timing.
   geometries.forEach((f,i)=>{
    let intersects=0,centre=0,whole=0,lo=Infinity,hi=0;
    if(!f?.groups||!f.right)throw Error('Renderer did not expose course projection');
    for(const places of f.groups.values())for(let j=0;j<places.length;j+=4){
     const [x,z,a,b]=places.slice(j,j+4),ax=x-f.aim[0],ay=224-f.aim[1],az=z-f.aim[2];
     const on=(v,limit,sign)=>Math.abs(ax*v[0]+ay*v[1]+az*v[2])<=limit+sign*(Math.abs(a*v[0]+b*v[2])*450+Math.abs(v[1])*240+Math.abs(-b*v[0]+a*v[2])*110);
     const inside=sign=>on(f.up,f.ext,sign)&&on(f.right,f.ext*f.w/f.h,sign);
     if(!inside(1))continue;
     intersects++;centre+=inside(0);whole+=inside(-1);
     const depth=ax*f.eye[0]+(214-f.aim[1])*f.eye[1]+az*f.eye[2],dist=f.ext/Math.tan(Math.PI/8);
     const px=700*f.h/(2*f.ext)*Math.max(.80,Math.min(1.25,dist/Math.max(50,dist-depth)));
     lo=Math.min(lo,px);hi=Math.max(hi,px);
    }
    frames[i].visible={intersects,centre,whole,min_span_px:lo,max_span_px:hi};
   });
   if(g.getError()!==g.NO_ERROR)throw Error('WebGL error after measured draw');
   return frames;
  }finally{queries.forEach(q=>g.deleteQuery(q));r.drawActors=original;}
 },states);
}

const mean=a=>a.reduce((t,n)=>t+n,0)/a.length;
const p95=a=>[...a].sort((a,b)=>a-b)[Math.ceil(a.length*.95)-1];
const round=n=>Math.round(n*1000)/1000;
function summarize(frames){
 const values=key=>frames.map(f=>f[key]);const gpu=values('gpu_ms').filter(Number.isFinite);
 const keys=new Set(frames.flatMap(f=>Object.keys(f.mix)));
 const range=a=>({min:Math.min(...a),mean:round(mean(a)),max:Math.max(...a)});
 const mix=Object.fromEntries([...keys].map(k=>[k,range(frames.map(f=>f.mix[k]||0))]));
 const visibility=Object.fromEntries(Object.keys(frames[0].visible).map(k=>[k,range(frames.map(f=>f.visible[k]))]));
 return {fps:round(1000/mean(values('interval_ms'))),p95_ms:round(p95(values('interval_ms'))),gpu_ms:gpu.length?round(mean(gpu)):null,gpu_samples:gpu.length,
  submit_ms:round(mean(values('submit_ms'))),draw_sync_ms:round(mean(values('sync_ms'))),triangles:range(values('triangles')),draw_calls:range(values('calls')),blits:range(values('blits')),mix,visibility};
}
const tune=JSON.parse(process.env.MEASURE_OPTIONS||'{}');
const rows=[];let environment={};
for(const [profile,{mobile,width,height,viewport,cpu}] of Object.entries(profiles)){
 if(filter && filter!==profile)continue;
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport,deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
  await page.addInitScript(instrument);await page.goto(url);await page.waitForFunction(()=>!!window.sLab,null,{timeout:120000});
  const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:cpu});
  const meta=await page.evaluate(async ({width,height})=>{sLab.manual(true);await sLab.ready();const canvas=sLab.renderer.canvas;canvas.style.width=width+'px';canvas.style.height=height+'px';const {stride,period}=sLab.meta;return {stride,period};},{width,height});
  const info=await page.evaluate(()=>{const g=sLab.renderer.gl,e=g.getExtension('WEBGL_debug_renderer_info');return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);});
  environment={chromium:browser.version(),renderer:info,dpr:1,animation_seconds:3,samples,sync_readback:'RGBA/UNSIGNED_BYTE, 1 x 1 center pixel after every frame',warmup:3,scenario:'v3/scenarios.js'};
  for(const key of Object.keys(RACES)){
   if(scenarioFilter && scenarioFilter!==key)continue;
   const states=Array.from({length:samples},(_,i)=>({...raceState(key,i/samples,width,height,meta),method,...tune}));
   await page.evaluate(async (states)=>{
    const r=sLab.renderer;
    if(states[0].method==='exact')await r.loadExact();
    if(states[0].method==='stack' && sLab.ensureStack)await sLab.ensureStack();
    // Cache exactly the elevation banks used by this camera. Asynchronous
    // downloads and construction are excluded from both steady-state timings.
    for(const id of new Set(states.map(s=>Math.round(s.tilt/10))))await r.sprites.load(id);
    Object.assign(sLab.state,states[0]);sLab.draw();await sLab.ready();
   },states);
   const frames=await measure(page,states);
   const row={profile,scenario:key,number:RACES[key],method,width,height,cpu,frames:frames.length,...summarize(frames),memory:await memory(browser,page,cdp),samples:frames};
   if(key.startsWith('near') && row.visibility.intersects.min!==RACES[key])throw Error('Near pack was clipped out of view');
   rows.push(row);console.log(version,profile,key,row.fps,row.p95_ms,row.gpu_ms,row.triangles.mean,row.draw_calls.mean,JSON.stringify(row.mix));
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.mkdir(path.dirname(destination),{recursive:true});await fs.writeFile(destination,JSON.stringify({version,environment,rows},null,1)+'\n');

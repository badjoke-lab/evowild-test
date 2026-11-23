// All measurements use one WebGL context in its original submission order.
// Consecutive draws from the same category share one non-nested GPU query.
export function installMeter(){
 let gl,ext,record,segment,query,queries=[],owners=new WeakMap(),visible;
 function end(){
   if(query){gl.endQuery(ext.TIME_ELAPSED_EXT);queries.push([record,segment,query]);query=null;}
   segment=null;
 }
 function group(name){
   if(!record||segment===name)return;
   end();segment=name;
   if(ext){query=gl.createQuery();gl.beginQuery(ext.TIME_ELAPSED_EXT,query);}
 }
 const meter={
   get active(){return !!record;},
   attach(renderer,racers,environment,ground){
     gl=renderer.getContext();ext=gl.getExtension('EXT_disjoint_timer_query_webgl2');
     for(const method of ['drawElementsInstanced','drawArraysInstanced']){
       const issue=gl[method];
       gl[method]=function(...args){
         if(record&&(segment==='pixelMesh'||segment==='sprite')){
           record.calls[segment]=(record.calls[segment]||0)+1;
           const count=method==='drawElementsInstanced'?args[1]:args[2],instances=args.at(-1);
           record.triangles[segment]=(record.triangles[segment]||0)+instances*(args[0]===gl.TRIANGLES?count/3:Math.max(0,count-2));
         }
         return issue.apply(this,args);
       };
     }
     for(const o of environment)o.traverse(child=>owners.set(child,{type:o===ground?'ground':'course'}));
     for(const r of racers)r.obj.traverse(child=>owners.set(child,{type:r.morph==='S'?'classicS':'otherMorph',id:r.id}));
     const draw=renderer.renderBufferDirect;
     renderer.renderBufferDirect=function(...args){
       if(!record)return draw.apply(this,args);
       const owner=owners.get(args[4])||{type:'sceneOther'};if(owner.id)visible.add(owner.id);
       group(owner.type);record.calls[owner.type]=(record.calls[owner.type]||0)+1;
       return meter.time(owner.type,()=>draw.apply(this,args));
     };
   },
   start(){
     record={cpu:{},gpu:{},calls:{},triangles:{}};visible=new Set();return record;
   },
   add(key,ms){record.cpu[key]=(record.cpu[key]||0)+ms;},
   time(name,callback){
     if(!record)return callback();
     if(name==='three')group('clearAndSetup');
     const start=performance.now();
     try{return callback();}finally{meter.add(name,performance.now()-start);if(name==='three')end();}
   },
   part(name,callback){
     if(!record)return callback();
     group(name);
     try{return meter.time(name,callback);}finally{end();}
   },
   stop(){
     end();record.nativeVisible=[...visible].sort((a,b)=>a-b);
     const t=performance.now();
     gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));
     record.cpu.wait=performance.now()-t;record=null;
   },
   async resolve(){
     if(!ext)throw Error('GPU timer not available');
     for(let i=0;queries.length&&!gl.getQueryParameter(queries.at(-1)[2],gl.QUERY_RESULT_AVAILABLE)&&i<300;i++)await new Promise(r=>setTimeout(r,5));
     if(gl.getParameter(ext.GPU_DISJOINT_EXT))throw Error('GPU disjoint');
     for(const [r,name,q] of queries){
       if(!gl.getQueryParameter(q,gl.QUERY_RESULT_AVAILABLE))throw Error('GPU sample unavailable');
       r.gpu[name]=(r.gpu[name]||0)+gl.getQueryParameter(q,gl.QUERY_RESULT)/1e6;gl.deleteQuery(q);
     }
     queries=[];
   }
 };
 window.ridgeMeter=meter;
}

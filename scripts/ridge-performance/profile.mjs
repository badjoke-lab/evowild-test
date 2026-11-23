import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {launch} from '../race-integration/browser.mjs';
import {installMeter} from './meter.mjs';
const screens={pc:{viewport:{width:1100,height:745},deviceScaleFactor:1},phone:{viewport:{width:390,height:844},deviceScaleFactor:2.625,isMobile:true,hasTouch:true}};
const [base,folder,tailFile]=process.argv.slice(2);
const tailFrames=tailFile?JSON.parse(await fs.readFile(tailFile,'utf8')):null;
const cases=process.env.RIDGE_CASE?.split(',');
const browser=await launch();
const sha=s=>createHash('sha256').update(s).digest('hex');
await fs.mkdir(folder,{recursive:true});
try{
 for(const [screen,options] of Object.entries(screens))for(const count of [100,18,50])for(const mode of ['pixel','classic']) {
   const prefix=[screen,count,mode,''].join('-');
   if((cases&&!cases.some(id=>id.startsWith(prefix)))||(tailFrames&&!Object.keys(tailFrames).some(id=>id.startsWith(prefix))))continue;
   const ctx=await browser.newContext(options),page=await ctx.newPage();
   if(process.env.RIDGE_ACTORS)await page.route('**/race-integration/probe-actors.js',route=>
     route.fulfill({path:process.env.RIDGE_ACTORS,contentType:'text/javascript'}));
   if(process.env.RIDGE_FLAT_COLOR==='1')await page.route('**/race-integration/probe-actors.js',async route=>{
     const original=await route.fetch(),source=await original.text();
     const seam='const next = program(gl, vs, fs);', color='color=vec4(palette[ink]*shade,1.);';
     if(!source.includes(seam))throw Error('Missing diagnostic shader seam');
     // Same geometry, dither, tests and depth writes. This control isolates
     // the marginal cost of computing the surface colour from its voxel.
     const replacement=`if(!far&&!fs.includes('${color}'))throw Error('Missing surface colour seam');
       const next=program(gl,vs,far?fs:fs.replace('${color}','color=vec4(1.);'));`;
     await route.fulfill({status:original.status(),contentType:'text/javascript',body:source.replace(seam,replacement)});
   });
   const errors=[];page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(installMeter);
   await page.goto(base+'probe.html?raceTrial=1&verify=1&count='+count+'&field='+(count===18?'mixed':'s')+'&look='+mode);
   await page.waitForFunction(pixel=>window.ridgePrepare&&(!pixel||raceSnapshot().pixels.ready),mode==='pixel');
   for(const camera of ['race','follow']){
     const id=[screen,count,mode,camera].join('-');
     if(cases&&!cases.includes(id)||tailFrames&&!tailFrames[id])continue;
     const {rows,shots,actors}=await page.evaluate(async({camera,frames})=>{
       const g=document.querySelector('#game').getContext('webgl2');
       const fence=()=>g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,new Uint8Array(4));
       const rows=[],shots=[],actors=[];
       for(const warm of [true,false]){
         ridgePrepare(camera);let prev=0;
         for(const n of frames){
           for(let j=prev+1;j<n;j++)ridgeAdvance();prev=n;
           fence();const row=warm?null:ridgeMeter.start();
           ridgeStep();
           if(row)ridgeMeter.stop();
           if(warm){
             // Wait for every requested exact angle before replay. Camera and
             // simulation have already been advanced to this diagnostic state.
             await new Promise(r=>setTimeout(r,130));
           }else{
             const {state,size,aa}=ridgeStatus();
             if(state.pixels.error||state.pixels.draw?.atlasErrors.length)throw Error('S asset failure');
             const {pixels,...game}=state;
             const drawn=pixels.draw;
             Object.assign(row,{frame:n,size,aa,streaming:drawn?.atlasPending??false,
               game:JSON.stringify(game),s:drawn?.details??[],lod:drawn?.mix??null});
             rows.push(row);
             const c=document.querySelector('#game');
             shots.push(c.toDataURL().split(',')[1]);actors.push(ridgeActorsPhoto());
           }
         }
         if(warm)await new Promise(r=>setTimeout(r,300));
       }
       await ridgeMeter.resolve();return {rows,shots,actors};
     },{camera,frames:tailFrames?.[id]??[25,41,57,73,89,105,120]});
     const imageDir=path.join(folder,'frames');await fs.mkdir(imageDir,{recursive:true});
     const actorDir=path.join(folder,'actors');await fs.mkdir(actorDir,{recursive:true});
     for(const [i,r] of rows.entries()){
       await fs.writeFile(path.join(actorDir,id+'-'+r.frame+'.png'),Buffer.from(actors[i],'base64'));
       r.state_sha=sha(r.game);delete r.game;
       r.actors_sha=sha(JSON.stringify(r.s));r.pixel_ids=r.s.map(s=>s.id);delete r.s;
       const png=Buffer.from(shots[i],'base64');
       await fs.writeFile(path.join(imageDir,id+'-'+r.frame+'.png'),png);
     }
     await fs.writeFile(path.join(folder,id+'.json'),JSON.stringify(rows)+'\n');
     const keys=new Set(rows.flatMap(r=>Object.keys(r.gpu)));
     const means=Object.fromEntries([...keys].map(k=>[k,(rows.reduce((a,r)=>a+(r.gpu[k]||0),0)/rows.length).toFixed(1)]));
     console.log(id,JSON.stringify(means), 'wait',Math.round(rows.reduce((a,r)=>a+r.cpu.wait,0)/rows.length));
   }
   if(errors.length)throw Error(errors);await ctx.close();
 }
}finally{await browser.close();}

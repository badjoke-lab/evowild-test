// Replay the actual race camera, movement and foot compensation. The two
// counterfactuals change submission only, never the number or pose of actors.
import {openLab,DEMO} from '../browser.mjs';
import {raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';
import fs from 'node:fs/promises';
import path from 'node:path';
const out=path.join(DEMO,'v4.1/evidence'),origin=process.env.LAB_BASE_URL||'http://127.0.0.1:4173/s-pixel-lab/';
const audit=[];
for(const version of ['v4','v4.1']){
 process.env.LAB_URL=origin+'v4.1/?version='+version;
 const {page,browser,errors}=await openLab({width:1280,height:900});
 try{
  const meta=await page.evaluate(async()=>{
   sLab.manual(true);sLab.renderer.fixedRaster={width:877,height:414};
   for(const bank of [1,2])await sLab.renderer.sprites.load(bank);return {stride:sLab.meta.stride,period:sLab.meta.period};
  });
  for(const key of ['mixed50','mixed100']){
   const states=Array.from({length:48},(_,i)=>raceState(key,i/48,877,414,meta));
   const result=await page.evaluate(({states,version})=>{
    const lab=sLab,r=lab.renderer,g=r.gl;
    const reference=new Uint8Array(877*414*4),test=new Uint8Array(reference.length);
    let cullPixels=0,coveragePixels=0,prunedMeshes=0,prunedCards=0,transitions=[];
    const read=buffer=>g.readPixels(0,0,877,414,g.RGBA,g.UNSIGNED_BYTE,buffer);
    const diff=()=>{let n=0;for(let i=0;i<test.length;i+=4)if(reference[i]!==test[i]||reference[i+1]!==test[i+1]||reference[i+2]!==test[i+2])n++;return n;};
    let png;
    for(let i=0;i<states.length;i++){
     Object.assign(lab.state,states[i],{frontFaces:true});lab.draw();read(reference);
     if(i===12)png=r.canvas.toDataURL().split(',')[1];
     if(version==='v4')continue;
     const optimized={...r.mix};
     r.effectiveCoverage=f=>f;
     try{lab.draw();read(test);coveragePixels+=diff();prunedMeshes+=optimized.sprite-r.mix.sprite;prunedCards+=optimized.mid-r.mix.mid;
      transitions.push({i,logical:r.mix.transition,submitted:optimized.transition,mesh_skips:optimized.sprite-r.mix.sprite});
     }finally{delete r.effectiveCoverage;}
     lab.state.frontFaces=false;lab.draw();read(test);cullPixels+=diff();
    }
    if(g.getError()!==g.NO_ERROR)throw Error('WebGL readback');
    return {png,cullPixels,coveragePixels,prunedMeshes,prunedCards,transitions};
   },{states,version});
   const {png,...record}=result;await fs.writeFile(path.join(out,version+'-'+key+'.png'),Buffer.from(png,'base64'));
   if(version==='v4.1')audit.push({key,...record});
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.writeFile(path.join(out,'submission-check.json'),JSON.stringify(audit,null,1)+'\n');
if(audit.some(a=>a.cullPixels||a.coveragePixels))throw Error('A submission optimization changed pixels: '+JSON.stringify(audit.map(a=>[a.key,a.cullPixels,a.coveragePixels])));

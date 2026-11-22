// Real buttons and pointer/touch events first; cold-angle test then samples a
// fixed state to distinguish transient loading from the endpoint appearance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';

const version=process.argv[2] || 'v3';
if(!['v3','v4'].includes(version))throw Error('Unknown UI version');
const evidence=path.join(DEMO,version,'evidence');
const results=[];
process.env.LAB_URL=(process.env.LAB_ORIGIN||'http://127.0.0.1:4173')+'/s-pixel-lab/'+version+'/';
for(const mobile of [false,true]){
 const {page,browser,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 const checks=[];
 try{
  await page.evaluate(()=>sLab.ready());
  const check=(name,ok)=>{assert.ok(ok,name);checks.push(name);};
  const clip=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
  check('viewport fits',clip<=1);
  await page.screenshot({path:path.join(evidence,mobile?'mobile.png':'desktop.png')});
  await page.locator('#play').click();await page.waitForFunction(()=>sLab.state.playing&&sLab.state.time>0);
  check('running clock',await page.evaluate(()=>sLab.state.time>0));
  await page.locator('#play').click();check('pause',await page.evaluate(()=>!sLab.state.playing));
  const scene=page.locator('#scene');
  await scene.scrollIntoViewIfNeeded();const box=await scene.boundingBox();
  const at={x:Math.round(box.x+box.width*.52),y:Math.round(box.y+box.height*.58)};
  const yaw=await page.evaluate(()=>sLab.state.yaw);
  if(mobile){
   const cdp=await page.context().newCDPSession(page);
   for(const [type,pts] of [['touchStart',[at]],['touchMove',[{x:at.x+37,y:at.y-24}]],['touchEnd',[]]]){
    await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:pts});
   }
  }else{
   await page.mouse.move(at.x,at.y);await page.mouse.down();await page.mouse.move(at.x+37,at.y-24);await page.mouse.up();
  }
  check(mobile?'touch orbit':'mouse orbit',await page.evaluate(()=>sLab.state.yaw)!==yaw);
  await page.locator('#method [data-method="stack"]').click();await page.evaluate(()=>sLab.ensureStack());
  check('128-layer stack',await page.evaluate(()=>sLab.state.method==='stack'));
  await page.locator('#method [data-method="surface"]').click();
  check('surface mode',await page.evaluate(()=>sLab.state.method==='surface'));
  await page.locator('#compare').click();
  await page.locator('#reference').waitFor({state:'visible'});
  check('side-by-side canvases',await scene.isVisible());
  await page.locator('#scene').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(evidence,mobile?'compare-mobile.png':'compare-desktop.png')});
  await page.locator('#compare').click();
  for(const [key,count] of [['near10',10],['mixed50',50],['mixed100',100],['overview100',100]]){
   await page.locator('#scenario [data-case="'+key+'"]').click();
   await page.waitForFunction(n=>sLab.state.number===n&&sLab.state.course,count);
   check('course '+key,await page.evaluate(()=>sLab.state.method==='lod'));
  }
  await page.locator('#reset').click();
  const cold=await page.evaluate(async()=>{
   const lab=sLab,r=lab.renderer,c=r.canvas;lab.manual(true);
   const snapshot=()=>{
    lab.draw();
    const raw=new Uint8Array(c.width*c.height*4);
    r.gl.readPixels(0,0,c.width,c.height,r.gl.RGBA,r.gl.UNSIGNED_BYTE,raw);return raw;
   };
   const compare=(a,b)=>{
    let both=0,either=0,r=0,s=0;
    for(let i=0;i<a.length;i+=4){
     const x=Math.max(a[i],a[i+1],a[i+2])>12,y=Math.max(b[i],b[i+1],b[i+2])>12;
     both+=x&&y;either+=x||y;r+=x;s+=y;
    }
    return {iou:both/Math.max(1,either),reference_px:r,candidate_px:s};
   };
   Object.assign(lab.state,{method:'stack',mask:true,number:1,course:false,idle:false,time:.43,tilt:89,
     yaw:-90,playing:false,spin:false,magnification:.28,samples:24,zoom:1});
   await lab.ensureStack();const stack=snapshot();
   const wasLoaded=!!r.sprites?.banks?.get(9)?.ready;
   lab.state.method='lod';const now=snapshot(),immediate={...r.mix};
   if(r.sprites?.load)await r.sprites.load(9);
   const after=snapshot(),settled={...r.mix};
   const answer={wasLoaded,immediate,settled,before:compare(stack,now),after:compare(stack,after),
     beforeAfter:compare(now,after),webgl:r.gl.getError()};
   return answer;
  });
  check('steep camera cut has a visible body during & after loading',cold.before.candidate_px>0&&cold.after.candidate_px>0);
  check('WebGL readback',cold.webgl===0);
  check('no browser errors',errors.length===0);
  results.push({profile:mobile?'touch emulation 390×844':'desktop 1280×900',checks,cold,errors});
 }finally{await browser.close();}
}
await fs.writeFile(path.join(evidence,'ui.json'),JSON.stringify(results,null,1));

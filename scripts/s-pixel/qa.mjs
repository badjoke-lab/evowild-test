import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {DEMO,openLab} from './browser.mjs';
const report={controls:[],artifacts:[],screens:[]};
for(const mobile of [false,true]){
 const {browser,page,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 try{
  const check=async(label,fn)=>{assert(await page.evaluate(fn),label);report.controls.push((mobile?'mobile / ':'desktop / ')+label);};
  await check('initial specimen',()=>sLab.state.idle&&sLab.draw()>0);
  await page.waitForTimeout(700);await page.screenshot({path:path.join(DEMO,'evidence',mobile?'mobile.png':'desktop.png'),fullPage:false});
  await page.locator('#play').click();await page.waitForTimeout(220);await check('play advances time',()=>sLab.state.playing&&sLab.state.time>0);
  await page.locator('#play').click();const t=await page.evaluate(()=>sLab.state.time);await page.waitForTimeout(120);assert.equal(await page.evaluate(()=>sLab.state.time),t);
  await page.locator('#mode button').last().click();await check('course motion',()=>sLab.state.course&&sLab.state.playing);
  await page.locator('#spin').click();const yaw=await page.evaluate(()=>sLab.state.yaw);await page.waitForTimeout(250);assert.notEqual(await page.evaluate(()=>sLab.state.yaw),yaw);
  await page.locator('#reset').click();await check('reset',()=>sLab.state.idle&&sLab.state.number===1&&!sLab.state.course);
  await page.locator('#samples button').first().click();await page.locator('#scrub').fill('7');await check('12-pose seek',()=>sLab.state.samples===12&&!sLab.state.idle&&!sLab.state.playing);
  for(const n of [10,50,100,1]){
   await page.locator('#number button',{hasText:new RegExp('^'+n+'$')}).click();
   assert.equal(await page.evaluate(()=>sLab.state.number),n);
  }
  for(const n of [16,32,64,128]){
   await page.locator('#layers button',{hasText:new RegExp('^'+n+'$')}).click();await page.evaluate(()=>sLab.ready());
   assert.equal(await page.evaluate(()=>sLab.state.layers),n);
  }
  await page.locator('#tiles button').nth(3).click();await check('top preset',()=>sLab.state.tilt===90);
  const rect=await page.locator('#scene').boundingBox();const [x,y]=[rect.x+rect.width/2,rect.y+rect.height/2];
  if(!mobile){
    await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+60,y+32);await page.mouse.up();
  }else{
    const cdp=await page.context().newCDPSession(page);
    await page.locator('#scene').scrollIntoViewIfNeeded();
    const r=await page.locator('#scene').boundingBox(),p={x:r.x+r.width/2,y:r.y+r.height/2};
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:p.x+54,y:p.y+36}]});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  }
  await check('camera drag',()=>sLab.state.tilt<90&&sLab.state.yaw!==0);
  await check('viewport fits',()=>document.documentElement.scrollWidth<=innerWidth+1);
  await check('WebGL error',()=>sLab.renderer.gl.getError()===0);
  if(!mobile){
   await page.evaluate(()=>{sLab.manual(true);sLab.renderer.canvas.style.width='360px';sLab.renderer.canvas.style.height='230px';});
   for(const layers of [16,32,64,128]){
    await page.evaluate(n=>sLab.selectLayers(n),layers);
    // 2° increments over a full turn. Temporal reversals measure a pixel that
    // changes occupancy for just one sample, including actual thin tips.
    const diag=await page.evaluate(()=>{
     const {renderer:r,state:s}=sLab,gl=r.gl,c=r.canvas,w=c.width,h=c.height;
     Object.assign(s,{mask:true,course:false,idle:true,number:1,zoom:.92});
     const pixels=new Uint8Array(w*h*4),res=[];
     const pop=(a)=>a.reduce((sum,x)=>sum+x,0);
     for(const tilt of [3,15,60]){
      s.tilt=tilt;let last,first,second,prev;let flips=0,total=0,max=0,pairs=0;
      const compare=(a,b,c)=>{let n=0,u=0;for(let i=0;i<a.length;i++){if(a[i]===c[i]&&a[i]!==b[i])n++;u+=a[i]|b[i]|c[i];}flips+=n;total+=u;max=Math.max(max,n/u);pairs++;};
      for(let k=0;k<180;k++){
       s.yaw=k*2;sLab.draw();gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
       const mask=new Uint8Array(w*h);
       for(let i=0;i<w*h;i++)mask[i]=pixels[4*i]||pixels[4*i+1]||pixels[4*i+2]?1:0;
       if(!pop(mask))throw Error('empty silhouette');
       if(k===0)first=mask;if(k===1)second=mask;if(k>=2)compare(prev,last,mask);prev=last;last=mask;
      }
      compare(prev,last,first);compare(last,first,second);
      res.push({tilt,steps:pairs,reversal_fraction:+(flips/total).toFixed(5),peak_fraction:+max.toFixed(5)});
     }return res;
    });
    report.artifacts.push({layers,rotation:diag});
   }
  }
  if(errors.length)throw Error(errors.join('\n'));
  report.screens.push({mobile,errors});
 }finally{await browser.close();}
}
await fs.writeFile(path.join(DEMO,'evidence/qa.json'),JSON.stringify(report,null,2));

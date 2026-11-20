import assert from 'node:assert/strict';
import path from 'node:path';
import fs from 'node:fs/promises';
import {openLab,DEMO} from '../browser.mjs';
process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/v2/';
const checks=[];
for(const mobile of [false,true]){
 const {page,browser,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 try{
  await page.locator('#play').click();await page.waitForTimeout(250);assert(await page.evaluate(()=>sLab.state.time>0));
  await page.locator('#spin').click();const yaw=await page.evaluate(()=>sLab.state.yaw);await page.waitForTimeout(250);assert.notEqual(await page.evaluate(()=>sLab.state.yaw),yaw);
  await page.locator('#reset').click();await page.locator('#number button').last().click();
  await page.waitForFunction(()=>sLab.renderer.mix.sprite===100);
  await page.locator('#mode button').last().click();assert(await page.evaluate(()=>sLab.state.course&&sLab.state.playing));
  await page.locator('#method [data-method="stack"]').click();assert.equal(await page.evaluate(()=>sLab.renderer.mix.near),100);
  await page.locator('#method [data-method="lod"]').click();
  await page.locator('#layers button').first().click();await page.evaluate(()=>sLab.ready());
  assert.equal(await page.evaluate(()=>sLab.state.layers),64);
  await page.locator('#number button').first().click();await page.locator('#method [data-method="sprite"]').click();
  await page.locator('#tilt').fill('87');await page.waitForFunction(()=>sLab.renderer.bank===9,{},{timeout:45000});
  await page.locator('#magnification').fill('0.25');assert.equal(await page.evaluate(()=>sLab.state.magnification),.25);
  await page.locator('#reset').click();await page.evaluate(()=>sLab.ready());
  const c=page.locator('#scene');await c.scrollIntoViewIfNeeded();const box=await c.boundingBox();
  const point={x:box.x+box.width/2,y:box.y+box.height/2};
  if(mobile){
   const cdp=await page.context().newCDPSession(page);
   for(const [type,points] of [['touchStart',[point]],['touchMove',[{x:point.x+42,y:point.y-25}]],['touchEnd',[]]])await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points});
  }else{
   await page.mouse.move(point.x,point.y);await page.mouse.down();await page.mouse.move(point.x+42,point.y-25);await page.mouse.up();
  }
  assert.notEqual(await page.evaluate(()=>sLab.state.yaw),-22);
  await page.locator('#tiles button').last().click();assert.equal(await page.evaluate(()=>sLab.state.yaw),-45);
  assert.equal(await page.evaluate(()=>sLab.renderer.gl.getError()),0);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.locator('#reset').click();await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(250);
  await page.screenshot({path:path.join(DEMO,'v2/evidence',mobile?'mobile.png':'desktop.png')});
  checks.push({mobile,errors,checks:['play','orbit','100 sprites','course','full stack','64 layers','uncached 90-degree bank','zoom','drag','quarter','WebGL','viewport']});
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.writeFile(path.join(DEMO,'v2/evidence/ui.json'),JSON.stringify(checks,null,2));

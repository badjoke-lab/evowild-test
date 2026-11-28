import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {launch} from '../race-integration/browser.mjs';
const origin=process.env.FORM_ORIGIN||'http://localhost:4186/evowild-test/';
const browser=await launch();const results=[];
try{
 for(const mobile of [false,true]){
  const page=await browser.newPage(mobile?{viewport:{width:390,height:844},deviceScaleFactor:2.625,isMobile:true,hasTouch:true}:{viewport:{width:1200,height:850}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin+'s-form.html');await page.waitForFunction(()=>window.formStudy?.ready);
  for(const yaw of [0,-90,90,-45]){
   await page.locator('[data-yaw="'+yaw+'"]').first().click();
   assert.equal(await page.evaluate(()=>formStudy.state.yaw),yaw);
  }
  await page.selectOption('#motion','run');await page.waitForTimeout(150);
  await page.locator('#pause').click();const t=await page.evaluate(()=>formStudy.state.time);
  await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>formStudy.state.time),t);
  await page.locator('#phase').fill('12');assert.equal(await page.evaluate(()=>formStudy.state.time),.36);
  await page.selectOption('#surface','clay');await page.screenshot({path:'public/s-form/evidence/studio-'+(mobile?'phone':'pc')+'.png'});
  const geometry=await page.evaluate(()=>{
   const f=formStudy,mesh=f.mesh,g=mesh.geometry,v=f.camera.position.clone(),minima=[];
   for(let phase=0;phase<24;phase++){
    Object.assign(f.state,{manual:true,idle:false,time:phase/24*.72});f.draw();let lowest=Infinity;
    for(let i=0;i<g.attributes.position.count;i++){
      mesh.getVertexPosition(i,v);if(!Number.isFinite(v.lengthSq()))throw Error('non-finite GLB vertex');lowest=Math.min(lowest,v.y);
    }minima.push(lowest);
   }
   return {vertices:g.attributes.position.count,morphs:g.morphAttributes.position.length,normals:g.morphAttributes.normal.length,lowest_vertex_y_m:minima,gl:f.renderer.getContext().getError()};
  });
  assert.equal(geometry.gl,0);assert.equal(geometry.morphs,24);assert.equal(geometry.normals,24);
  assert.ok(Math.min(...geometry.lowest_vertex_y_m)>-1e-6);
  assert.deepEqual(errors,[]);results.push({mobile,geometry});await page.close();
 }
 await fs.writeFile('public/s-form/evidence/ui-check.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}

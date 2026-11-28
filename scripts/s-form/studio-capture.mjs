import fs from 'node:fs/promises';
import {launch} from '../race-integration/browser.mjs';
const root=process.env.FORM_WORK||'/tmp/evowild-s-form';
await fs.mkdir(root,{recursive:true});
const browser=await launch(),page=await browser.newPage({viewport:{width:1100,height:800}});
page.on('pageerror',e=>console.error(e));
await page.goto((process.env.FORM_ORIGIN||'http://localhost:4185/evowild-test/')+'s-form.html');
await page.waitForFunction(()=>window.formStudy?.ready);
for(const [key,yaw,tilt] of [['side',0,0],['front',-90,0],['rear',90,0],['top',0,90],['quarter',-45,10]]){
 const data=await page.evaluate(({yaw,tilt})=>{
   Object.assign(formStudy.state,{manual:true,idle:true,width:1000,height:650,ground:false,yaw,tilt});formStudy.draw();
   return formStudy.renderer.domElement.toDataURL().split(',')[1];
 },{yaw,tilt});
 await fs.writeFile(root+'/'+key+'.png',Buffer.from(data,'base64'));
}
for(const phase of [0,6,12,18]){
 const data=await page.evaluate(phase=>{Object.assign(formStudy.state,{idle:false,time:phase/24*.72,yaw:-45,tilt:10});formStudy.draw();return formStudy.renderer.domElement.toDataURL().split(',')[1]},phase);
 await fs.writeFile(root+'/run-'+phase+'.png',Buffer.from(data,'base64'));
}
await browser.close();

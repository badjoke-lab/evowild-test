import {test,expect} from '@playwright/test';import fs from 'node:fs';import zlib from 'node:zlib';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';
const url='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v2';
const open=async page=>{await page.goto(url);await page.waitForFunction(()=>window.sRunReview);await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});};
test('D3-C v2 authored GLB preserves real sole contact across seven speed profiles',async({page},info)=>{
 test.setTimeout(300000);await open(page);
 for(const profile of [...[.5,1,1.5].map(r=>({name:'steady-'+r,phase:0,mode:'step',knots:[[0,r],[1,r]]})),...profiles]){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true,recordBody:true});const r=summarizeToeProfile(trace);
  console.log('D3C_V2_CONTACT',JSON.stringify(r));
  if(process.env.D3C_OUT&&info.project.name==='desktop-chromium'){fs.mkdirSync(process.env.D3C_OUT,{recursive:true});fs.writeFileSync(`${process.env.D3C_OUT}/v2-${profile.name}.json.gz`,zlib.gzipSync(JSON.stringify(trace)));fs.writeFileSync(`${process.env.D3C_OUT}/v2-${profile.name}-summary.json`,JSON.stringify(r,null,2));}
  for(const f of r.feet){expect(f.maxMeshVelocityResidual).toBeLessThan(.02);expect(f.maxZeroTimeJump).toBeLessThan(.001);expect(f.guardPenetration).toBeLessThan(.001);expect(f.maxReachError).toBeLessThan(.001);expect(f.supportSlip).toBeLessThan(.001);expect(f.maxSupportPlaneError).toBeLessThan(.001);expect(f.recoveryHeight).toBeGreaterThan(f.name.startsWith('hind')?.44:.30);expect(f.jointAngleRange[0]).toBeGreaterThan(35);expect(f.jointAngleRange[1]).toBeLessThan(178);expect(f.maxSegmentLengthDrift).toBeLessThan(.00001);}
 }
});
test('D3-C v2 sampled skin freezes and repeated dt0 does not accumulate shoulder glide',async({page})=>{
 await open(page);const r=await page.evaluate(()=>{const s=window.sRunReview,ids=Array.from({length:310},(_,i)=>i*125),dist=(a,b)=>Math.max(...a.map((v,i)=>Math.hypot(...v.map((x,j)=>x-b[i][j]))));let jump=0,freeze=0,repeat=0;
  for(const phase of [.2,.32,.64,.75,.9]){s.setRate(.5);s.setPhase(phase,'SIDE',false);const start=s.probe(ids);for(let i=0;i<10;i++)s.step(0);repeat=Math.max(repeat,dist(start,s.probe(ids)));s.setRate(1.5);s.step(0);jump=Math.max(jump,dist(start,s.probe(ids)));s.setRate(0);s.step(.5);freeze=Math.max(freeze,dist(start,s.probe(ids)));}return {jump,freeze,repeat,asset:s.sample().asset,bones:s.sample().bones};
 });console.log('D3C_V2_FREEZE',JSON.stringify(r));expect(r.asset).toContain('author-v2.glb');expect(r.bones).toBe(23);expect(r.jump).toBeLessThan(.001);expect(r.freeze).toBeLessThan(.001);expect(r.repeat).toBeLessThan(.000001);
});
test('D3-C v2 recovery articulates elbow and body skin versus preserved v1',async({page})=>{
 test.setTimeout(90000);const variants=[];for(const version of ['authored-v1','authored-v2']){await page.goto(url.replace('authored-v2',version));await page.waitForFunction(()=>window.sRunReview);variants.push(await page.evaluate(()=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview;return [.2,.32,.64,.75,.9].map(phase=>{s.setRate(1);s.setPhase(phase,'SIDE',false);return {phase,limbs:s.motionSample().contact.limbs,skin:s.probe(s.bodyVertexIds)};});}));}
 let fold=0,bodyDelta=0;variants[0].forEach((a,i)=>{const b=variants[1][i];for(let j=0;j<2;j++)fold=Math.max(fold,a.limbs[j].jointAngles[0]-b.limbs[j].jointAngles[0]);for(let k=0;k<a.skin.length;k++)bodyDelta=Math.max(bodyDelta,Math.hypot(...a.skin[k].map((x,j)=>x-b.skin[k][j])));});console.log('D3C_V2_ARTICULATION',JSON.stringify({fold,bodyDelta}));expect(fold).toBeGreaterThan(15);expect(bodyDelta).toBeGreaterThan(.02);expect(bodyDelta).toBeLessThan(.25);
});
test('D3-C v2 sampled body and fore skin retain velocity continuity at speed commands',async({page})=>{
 await open(page);const rows=await page.evaluate(()=>{const s=window.sRunReview,h=1e-5,ids=Array.from({length:310},(_,i)=>i*125),result=[];
  for(const phase of [.2,.32,.64,.7,.75,.9])for(const [from,to] of [[.5,1.5],[1.5,.5]]){s.setRate(from);s.setPhase(phase-h*2.4*Math.sqrt(from),'SIDE',false);const a=s.probe(ids);s.step(h);const before=s.probe(ids);s.setRate(to);s.step(0);const at=s.probe(ids);s.step(h);const after=s.probe(ids);result.push({phase,from,to,jump:Math.max(...at.map((p,i)=>Math.hypot(...p.map((v,j)=>v-before[i][j])))),residual:Math.max(...at.map((p,i)=>Math.hypot(...p.map((v,j)=>(after[i][j]-v)/h-(before[i][j]-a[i][j])/h))))});}return result;
 });console.log('D3C_V2_BODY_VELOCITY',JSON.stringify(rows));for(const r of rows){expect(r.jump).toBeLessThan(.001);expect(r.residual).toBeLessThan(.02);}
});

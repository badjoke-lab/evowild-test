import {test,expect} from '@playwright/test';import fs from 'node:fs';import zlib from 'node:zlib';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';
const url='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v3';
const open=async page=>{await page.goto(url);await page.waitForFunction(()=>window.sRunReview);await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});};
test('D3-C v3 authored GLB preserves real sole contact across seven speed profiles',async({page},info)=>{
 test.setTimeout(300000);await open(page);
 for(const profile of [...[.5,1,1.5].map(r=>({name:'steady-'+r,phase:0,mode:'step',knots:[[0,r],[1,r]]})),...profiles]){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true,recordBody:true});const r=summarizeToeProfile(trace);
  console.log('D3C_V3_CONTACT',JSON.stringify(r));
  if(process.env.D3C_OUT&&info.project.name==='desktop-chromium'){fs.mkdirSync(process.env.D3C_OUT,{recursive:true});fs.writeFileSync(`${process.env.D3C_OUT}/v3-${profile.name}.json.gz`,zlib.gzipSync(JSON.stringify(trace)));fs.writeFileSync(`${process.env.D3C_OUT}/v3-${profile.name}-summary.json`,JSON.stringify(r,null,2));}
  for(const f of r.feet){expect(f.maxMeshVelocityResidual).toBeLessThan(.02);expect(f.maxZeroTimeJump).toBeLessThan(.001);expect(f.guardPenetration).toBeLessThan(.001);expect(f.maxReachError).toBeLessThan(.001);expect(f.supportSlip).toBeLessThan(.001);expect(f.maxSupportPlaneError).toBeLessThan(.001);expect(f.recoveryHeight).toBeGreaterThan(f.name.startsWith('hind')?.44:.30);expect(f.jointAngleRange[0]).toBeGreaterThan(35);expect(f.jointAngleRange[1]).toBeLessThan(178);expect(f.maxSegmentLengthDrift).toBeLessThan(.00001);}
 }
});
test('D3-C v3 sampled skin freezes and repeated dt0 does not accumulate shoulder glide',async({page})=>{
 await open(page);const r=await page.evaluate(()=>{const s=window.sRunReview,ids=Array.from({length:310},(_,i)=>i*125),dist=(a,b)=>Math.max(...a.map((v,i)=>Math.hypot(...v.map((x,j)=>x-b[i][j]))));let jump=0,freeze=0,repeat=0;
  for(const phase of [.2,.32,.64,.72,.75,.9]){s.setRate(.5);s.setPhase(phase,'SIDE',false);const start=s.probe(ids);for(let i=0;i<10;i++)s.step(0);repeat=Math.max(repeat,dist(start,s.probe(ids)));s.setRate(1.5);s.step(0);jump=Math.max(jump,dist(start,s.probe(ids)));s.setRate(0);s.step(.5);freeze=Math.max(freeze,dist(start,s.probe(ids)));}return {jump,freeze,repeat,asset:s.sample().asset,bones:s.sample().bones};
 });console.log('D3C_V3_FREEZE',JSON.stringify(r));expect(r.asset).toContain('author-v3.glb');expect(r.bones).toBe(23);expect(r.jump).toBeLessThan(.001);expect(r.freeze).toBeLessThan(.001);expect(r.repeat).toBeLessThan(.000001);
});
test('D3-C v3 unfolds the leading foreleg while preserving v2 body and rear pose',async({page})=>{
 test.setTimeout(90000);const poses=[];
 for(const version of ['authored-v2','authored-v3']){
  await page.goto(url.replace('authored-v3',version));await page.waitForFunction(()=>window.sRunReview);poses.push(await page.evaluate(()=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview;s.setRate(1);return [.14,.20,.25,.28,.307,.32,.35,.40,.473].map(phase=>{s.setPhase(phase,'SIDE',false);return {phase,body:s.probe(s.bodyVertexIds),contact:s.motionSample().contact,soles:s.soleSample()};});}));
 }
 let bodyDrift=0,hindDrift=0;for(let i=0;i<poses[0].length;i++){const a=poses[0][i],b=poses[1][i];for(let j=0;j<a.body.length;j++)bodyDrift=Math.max(bodyDrift,Math.hypot(...a.body[j].map((x,k)=>x-b.body[j][k])));for(let foot=2;foot<4;foot++)for(let j=0;j<a.soles[foot].points.length;j++)hindDrift=Math.max(hindDrift,Math.hypot(...a.soles[foot].points[j].map((x,k)=>x-b.soles[foot].points[j][k])));}
 const old=poses[0][4].contact.limbs,now=poses[1][4].contact.limbs;
 console.log('D3C_V3_RECOVERY',JSON.stringify({bodyDrift,hindDrift,at307:now.slice(0,2).map(l=>({name:l.name,elbow:l.jointAngles[0],endpoint:l.joints.at(-1)}))}));
 expect(bodyDrift).toBeLessThan(1e-6);expect(hindDrift).toBeLessThan(1e-6);
 for(let i=0;i<2;i++)expect(now[i].jointAngles[0]-old[i].jointAngles[0]).toBeGreaterThan(10);
 expect(Math.min(...poses[1].map(p=>p.contact.limbs[0].jointAngles[0]))).toBeGreaterThan(80);
 expect(Math.min(...poses[1].map(p=>p.contact.limbs[1].jointAngles[0]))).toBeGreaterThan(70);
});
test('D3-C v3 sampled body and fore skin retain velocity continuity at speed commands',async({page})=>{
 await open(page);const rows=await page.evaluate(()=>{const s=window.sRunReview,h=1e-5,ids=Array.from({length:310},(_,i)=>i*125),result=[];
  for(const phase of [.14,.2,.25,.307,.32,.4,.473,.64,.7,.71199,.712,.71201,.72,.72799,.728,.72801,.75,.81,.89,.9])for(const [from,to] of [[.5,1.5],[1.5,.5]]){s.setRate(from);s.setPhase(phase-h*2.4*Math.sqrt(from),'SIDE',false);const a=s.probe(ids);s.step(h);const before=s.probe(ids);s.setRate(to);s.step(0);const at=s.probe(ids);s.step(h);const after=s.probe(ids);result.push({phase,from,to,jump:Math.max(...at.map((p,i)=>Math.hypot(...p.map((v,j)=>v-before[i][j])))),residual:Math.max(...at.map((p,i)=>Math.hypot(...p.map((v,j)=>(after[i][j]-v)/h-(before[i][j]-a[i][j])/h))))});}return result;
 });console.log('D3C_V3_BODY_VELOCITY',JSON.stringify(rows));for(const r of rows){expect(r.jump).toBeLessThan(.001);expect(r.residual).toBeLessThan(.02);}
});

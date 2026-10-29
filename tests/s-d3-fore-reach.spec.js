import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {test,expect} from '@playwright/test';
import {profiles,captureContactProfile} from '../scripts/s_contact_profiles.mjs';
import {summarizeToeProfile} from '../scripts/s_toe_metrics.mjs';
const base='/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=';

async function pose(page,variant,phase,rate=1){
 await page.goto(base+variant);
 await page.waitForFunction(()=>window.sRunReview?.bodyVertexIds?.length>0);
 return page.evaluate(({phase,rate})=>{
  const a=window.sRunReview;
  window.requestAnimationFrame=()=>0;
  a.setRate(rate);a.setPhase(phase,'SIDE',false);
  const motion=a.motionSample();
  const body=a.bodySample();
  return {legs:motion.contact.limbs.map(l=>({
   name:l.name,stage:l.stage,anchor:l.anchor,reach:l.reachError,
   foot:l.joints.at(-1),visualReach:l.foreVisualReach||0
  })),chest:body.find(b=>b.name==='chest').quaternion,
  spine:body.find(b=>b.name==='spine').quaternion};
 },{phase,rate});
}

test('D3-B isolated fore swing improves reach without moving a support anchor',async({page})=>{
 test.setTimeout(120000);
 for(const rate of [.5,1,1.5]){
  const before=await pose(page,'push-v3',.20,rate);
  const after=await pose(page,'push-v5',.20,rate);
  const fore=before.legs.filter(l=>l.name.startsWith('fore_'));
  const delta=fore.map(b=>{
   const a=after.legs.find(x=>x.name===b.name);
   return {name:b.name,stage:b.stage,deltaZ:a.foot[2]-b.foot[2],reach:a.visualReach};
  });
  console.log('D3B_FORE_SWING',JSON.stringify({rate,delta}));
  expect(delta.some(x=>x.reach>.025)).toBe(true);
  expect(delta.some(x=>x.deltaZ>.012)).toBe(true);
  for(const leg of after.legs){
   if(leg.anchor)expect(leg.visualReach).toBe(0);
   expect(leg.reach).toBeLessThan(.001);
  }
 }
});

test('D3-B chest load is localized to front support and preserves native outside pose',async({page})=>{
 test.setTimeout(120000);
 const ang=(a,b)=>2*Math.acos(Math.max(-1,Math.min(1,Math.abs(a.reduce((sum,x,i)=>sum+x*b[i],0)))))*180/Math.PI;
 for(const phase of [.53,.75,.96]){
  const a=await pose(page,'push-v3',phase,1.5);
  const b=await pose(page,'push-v5',phase,1.5);
  const change=ang(a.chest,b.chest);
  console.log('D3B_CHEST_LOAD',JSON.stringify({phase,change}));
  if(phase===.75)expect(change).toBeGreaterThan(2);
  else expect(change).toBeLessThan(.02);
 }
});

test('D3-B review keeps sole-contact guards on steady and abrupt speeds',async({page},testInfo)=>{
 test.setTimeout(240000);
 await page.goto(base+'push-v5');await page.waitForFunction(()=>window.sRunReview?.footSample);
 const choices=[
  {name:'steady-0.5',phase:0,mode:'step',knots:[[0,.5],[1,.5]]},
  {name:'steady-1',phase:0,mode:'step',knots:[[0,1],[1,1]]},
  {name:'steady-1.5',phase:0,mode:'step',knots:[[0,1.5],[1,1.5]]},
  ...profiles
 ];
 for(const profile of choices){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true,recordBody:!!process.env.S_D3B_EVIDENCE});
  const r=summarizeToeProfile(trace);
  if(process.env.S_D3B_EVIDENCE&&testInfo.project.name==='desktop-chromium'){
   const out=process.env.S_D3B_EVIDENCE;fs.mkdirSync(out,{recursive:true});fs.writeFileSync(`${out}/fixed-${profile.name}.json.gz`,gzipSync(JSON.stringify(trace)));
   fs.writeFileSync(`${out}/fixed-${profile.name}-summary.json`,JSON.stringify(r,null,2)+'\n');
  }
  for(const foot of r.feet){
   expect(foot.maxZeroTimeJump).toBeLessThan(.001);
   expect(foot.maxMeshVelocityResidual).toBeLessThan(.02);
   expect(foot.guardPenetration).toBeLessThan(.001);
   expect(foot.maxReachError).toBeLessThan(.001);
   expect(foot.supportSlip).toBeLessThan(.001);
   expect(foot.maxSupportPlaneError).toBeLessThan(.001);
   expect(foot.recoveryHeight).toBeGreaterThan(foot.name.startsWith('hind')?.44:.30);
  }
  console.log('D3B_CONTACT',JSON.stringify({profile:profile.name,feet:r.feet.map(f=>({name:f.name,reach:f.maxReachError,slip:f.supportSlip,jump:f.maxZeroTimeJump,clearance:f.maxSupportPlaneError}))}));
 }
});


test('D3-B speed commands preserve actual fore-sole and chest-mesh velocity through swing and support',async({page})=>{
 await page.goto(base+'push-v5');await page.waitForFunction(()=>window.sRunReview?.bodyVertexIds?.length);
 const rows=await page.evaluate(()=>{
  window.requestAnimationFrame=()=>0;const a=window.sRunReview,out=[],ids=[...a.bodyVertexIds,...a.solePatches.flatMap(p=>p.indices)];
  for(const rate of [.5,1,1.5])for(const phase of [.40506096654409807,.58,.64,.75,.81,.89,.94]){
   const eps=1e-5;a.setRate(rate);a.setPhase(phase-2.4*Math.sqrt(rate)*eps,'SIDE',false);const p=a.probe(ids);a.step(eps);const q=a.probe(ids);a.setRate(rate===1.5?.5:1.5);a.step(0);const q2=a.probe(ids);a.step(eps);const r=a.probe(ids);
   const velocity=Math.max(...q.map((v,i)=>Math.hypot(...v.map((x,j)=>(r[i][j]-q2[i][j]-x+p[i][j])/eps))));
   const jump=Math.max(...q.map((v,i)=>Math.hypot(...v.map((x,j)=>x-q2[i][j]))));
   a.setRate(0);a.step(0);const f=a.probe(ids);a.step(.3);const still=a.probe(ids);
   out.push({rate,phase,velocity,jump,freeze:Math.max(...f.map((v,i)=>Math.hypot(...v.map((x,j)=>x-still[i][j]))))});
  }return out;
 });
 for(const r of rows){expect(r.velocity).toBeLessThan(.02);expect(r.jump).toBeLessThan(.001);expect(r.freeze).toBeLessThan(1e-7);}
 console.log('D3B_SPEED_CONTINUITY',JSON.stringify(rows));
});

test('D3-B posture response preserves D2-D travel, cadence and contact-anchor evolution',async({page})=>{
 const data=[];
 for(const body of ['push-v3','push-v5']){
  await page.goto(base+body);await page.waitForFunction(()=>window.sRunReview?.footSample);
  data.push(await page.evaluate(()=>{
   window.requestAnimationFrame=()=>0;const a=window.sRunReview;a.setRate(.5);a.setPhase(.2,'SIDE',false);const rows=[];
   for(let i=0;i<240;i++){
    a.setRate(i<30?.5:i<130?1.5:.5);a.step(1/240);const c=a.motionSample().contact;
    rows.push({cycles:c.cycles,distance:c.distance,effectiveRate:c.effectiveRate,anchors:c.limbs.map(l=>l.anchor),stages:c.limbs.map(l=>l.stage),hind:a.motionSample().soles.slice(2).map(s=>s.points)});
   }return rows;
  }));
 }
 for(let i=0;i<data[0].length;i++){
  const b=data[0][i],a=data[1][i];for(const key of ['cycles','distance','effectiveRate','anchors','stages'])expect(a[key]).toEqual(b[key]);
  a.hind.forEach((foot,j)=>foot.forEach((p,k)=>expect(Math.hypot(...p.map((v,d)=>v-b.hind[j][k][d]))).toBeLessThan(.000001)));
 }
});

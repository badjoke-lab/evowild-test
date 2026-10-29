import fs from 'node:fs';import {chromium} from 'playwright';
const out='docs/2p5d/evidence/20261029-s-d3b-fore-reach',label=process.argv.includes('--after')?'fixed':'failed';
fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage();const reports=[];
for(const body of ['push-v3','push-v5']){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body='+body);await page.waitForFunction(()=>window.sRunReview);
 reports.push({body,...await page.evaluate(()=>{
  window.requestAnimationFrame=()=>0;const a=window.sRunReview,out=[];
  const snapshot=()=>({state:a.motionSample(),body:a.bodySample(),bodyPoints:a.probe(a.bodyVertexIds)});
  const velocity=(l,m,r,eps)=>m.map((p,i)=>Math.hypot(...p.map((v,j)=>(r[i][j]-2*v+l[i][j])/eps)));
  for(const phase of [.40506096654409807,.75])for(const eps of [1e-4,1e-5,1e-6]){
   a.setRate(.5);a.setPhase(phase-2.4*Math.sqrt(.5)*eps,'SIDE',false);const left=snapshot();a.step(eps);const mid=snapshot();a.setRate(1.5);a.step(0);const command=snapshot();a.step(eps);const right=snapshot();
   out.push({phase,eps,left,mid,command,right,soleResiduals:mid.state.soles.map((f,i)=>Math.max(...velocity(left.state.soles[i].points,f.points,right.state.soles[i].points,eps))),bodyResidual:Math.max(...velocity(left.bodyPoints,mid.bodyPoints,right.bodyPoints,eps))});
  }
  return {bodyVertexIds:a.bodyVertexIds,probes:out};
 })});
}
fs.writeFileSync(`${out}/${label}-speed-probes.json`,JSON.stringify(reports)+'\n');for(const r of reports)console.log(r.body,r.probes.map(p=>({phase:p.phase,eps:p.eps,sole:p.soleResiduals,body:p.bodyResidual})));await browser.close();

import {chromium} from 'playwright';import fs from 'node:fs';
const out='docs/2p5d/evidence/20261117-s-d3c-v3';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']}),page=await browser.newPage(),rows=[];
for(const variant of ['authored-v2','authored-v3']){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder='+variant);await page.waitForFunction(()=>window.sRunReview);
 rows.push(...await page.evaluate(variant=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview,ids=Array.from({length:310},(_,i)=>i*125),rows=[],h=1e-5;
  for(const phase of [.7199,.72,.7201])for(const [from,to] of [[.5,.5],[1.5,1.5],[.5,1.5],[1.5,.5]]){
   s.setRate(from);s.setPhase(phase-h*2.4*Math.sqrt(from),'SIDE',false);const a=s.probe(ids);s.step(h);const b=s.probe(ids);s.setRate(to);s.step(0);const c=s.probe(ids);s.step(h);const d=s.probe(ids);
   const values=c.map((p,i)=>Math.hypot(...p.map((x,j)=>(d[i][j]-x)/h-(b[i][j]-a[i][j])/h))),max=Math.max(...values),index=values.indexOf(max);
   rows.push({variant,phase,from,to,residual:max,vertex:ids[index],samples:[a[index],b[index],c[index],d[index]]});
  }return rows;
 },variant));
}
fs.writeFileSync(out+'/boundary-probe.json',JSON.stringify(rows,null,2));console.log(JSON.stringify(rows.filter(r=>r.phase===.72),null,2));await browser.close();

import {chromium} from 'playwright';import fs from 'node:fs';
const out='docs/2p5d/evidence/20261117-s-d3c-v3',browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']}),page=await browser.newPage(),variants=[];
for(const version of [2,3]){
 await page.goto(`http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v${version}`);await page.waitForFunction(()=>window.sRunReview);
 variants.push(await page.evaluate(()=>{window.requestAnimationFrame=()=>0;const s=window.sRunReview;s.setRate(1);return Array.from({length:21},(_,i)=>.710+i*.001).map(phase=>{s.setPhase(phase,'SIDE',false);return {phase,body:s.bodySample(),skin:s.probe(s.bodyVertexIds)};});}));
}
const dist=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i]));
const rows=variants[0].map((a,i)=>{const b=variants[1][i];return {phase:a.phase,rootDifference:dist(a.body[0].position,b.body[0].position),maxBodyBoneDifference:Math.max(...a.body.map((p,j)=>dist(p.position,b.body[j].position))),maxActualBodySkinDifference:Math.max(...a.skin.map((p,j)=>dist(p,b.skin[j])))};});
fs.writeFileSync(out+'/native-join-extent.json',JSON.stringify({rate:1,rows,maxRootDifference:Math.max(...rows.map(r=>r.rootDifference)),maxActualBodySkinDifference:Math.max(...rows.map(r=>r.maxActualBodySkinDifference)),variants},null,2));console.log(JSON.stringify({maxRootDifference:Math.max(...rows.map(r=>r.rootDifference)),maxActualBodySkinDifference:Math.max(...rows.map(r=>r.maxActualBodySkinDifference))}));await browser.close();

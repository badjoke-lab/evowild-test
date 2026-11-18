import {chromium,devices} from 'playwright';
const out='docs/2p5d/evidence/20261028-s-body-d2b',browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
for(const [device,options] of [['desktop',{viewport:{width:1280,height:800}}],['android',devices['Pixel 7']]]){
 const p=await browser.newPage(options);
 for(const [label,query] of [['before',''],['after','&body=push-v1']]){
  await p.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v2'+query);await p.waitForFunction(()=>window.sRunReview);
  await p.evaluate(()=>{window.requestAnimationFrame=()=>0;window.sRunReview.setRate(1);window.sRunReview.setPhase(.35,'REAR_3_4');});await p.screenshot({path:`${out}/${device}-push-${label}.png`});
 }await p.close();
}await browser.close();

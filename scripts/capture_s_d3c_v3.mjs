import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {chromium} from 'playwright';
const out='docs/2p5d/evidence/20261117-s-d3c-v3',previous='docs/2p5d/evidence/20261117-s-d3c-v2';
const views=['SIDE','FRONT','CHASE','LOW','REAR_3_4'],phases=[.14,.20,.25,.28,.307,.32,.35,.40,.473];
const priorDense=fs.existsSync(`${out}/dense-observations.json`)?JSON.parse(fs.readFileSync(`${out}/dense-observations.json`,'utf8')).records.filter(r=>r.label==='before'):[];
const reuseDense=priorDense.length===45&&views.every(view=>phases.every(p=>fs.existsSync(`${out}/dense/before-${view}/${p.toFixed(3)}.png`)));
fs.mkdirSync(out,{recursive:true});
// Byte-reuse completed v2 full-cycle capture: identical camera, phase .64, 1x.
for(const view of views){fs.copyFileSync(`${previous}/after-${view}.mp4`,`${out}/before-${view}.mp4`);fs.cpSync(`${previous}/frames/after-${view}`,`${out}/frames/before-${view}`,{recursive:true});}
for(const device of ['desktop','android'])fs.copyFileSync(`${previous}/${device}-after.png`,`${out}/${device}-before.png`);
const capture=spawnSync(process.execPath,['scripts/capture_s_motion_compare.mjs'],{env:{...process.env,S_COMPARE_OUT:out,S_COMPARE_BEFORE:'',S_COMPARE_AFTER:'&toe=roll-v3&body=push-v5&shoulder=authored-v3'},encoding:'utf8'});
if(capture.status)throw Error(capture.stderr||capture.stdout);
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']}),page=await browser.newPage({viewport:{width:960,height:640}}),records=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
for(const [label,version] of [['before',2],['after',3]]){
 if(label==='before'&&reuseDense){records.push(...priorDense);continue;}
 await page.goto(`http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v${version}`);await page.waitForFunction(()=>window.sRunReview);await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const view of views){const dir=`${out}/dense/${label}-${view}`;fs.mkdirSync(dir,{recursive:true});for(const phase of phases){
  const r=await page.evaluate(({view,phase})=>{const s=window.sRunReview;s.setRate(1);s.setPhase(phase,view);return {asset:s.sample().asset,state:s.motionSample()};},{view,phase});records.push({label,view,phase,...r});await page.screenshot({path:`${dir}/${phase.toFixed(3)}.png`});
 }}
}
fs.writeFileSync(`${out}/dense-observations.json`,JSON.stringify({errors,phases,records}));
fs.writeFileSync(`${out}/capture-provenance.json`,JSON.stringify({baseline:previous,reusedV2FullCycleFrames:120,newV3FullCycleFrames:120,reusedV2DenseFrames:reuseDense?45:0,newDenseFrames:reuseDense?45:90,views,phases,rate:1,cycleStart:.64,stepsPerCycle:24,stepSeconds:1/2.4/24,description:'Actual WebGL simulation-time capture, no interpolation. V2 full cycles/device stills copied byte-for-byte from already completed evidence; existing unchanged v2 dense captures reused when present. Pixel7 is emulation, not physical-device performance.'},null,2));await browser.close();

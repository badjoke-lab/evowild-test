import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {root,base,evidence,launch,fixedClock,ready} from '../race-integration/browser.mjs';

const original=execFileSync('git',['show','175b2bda4b63fa8a141b5b5c2674d6fb59e2d119:src/main.js'],{cwd:root,encoding:'utf8'});
const current=await fs.readFile(path.join(root,'src/main.js'),'utf8');
const between=(s,start,end)=>s.slice(s.indexOf(start),s.indexOf(end));
const sha=data=>createHash('sha256').update(data).digest('hex');
const core=s=>between(s,'const ranks =','function setCamera()');
assert.equal(core(original),core(current));
assert.equal(between(original,'  if (lab) {\n    camera.up','function updateHud'),between(current,'  if (lab) {\n    camera.up','function updateHud'));
const browser=await launch(),manifest={engine_sha256:sha(core(current)),cases:[]};
const screenshotFolder=process.env.TRIAL_SHOTS;
if(screenshotFolder)await fs.mkdir(screenshotFolder,{recursive:true});
async function run(n,field,mode){
  const page=await browser.newPage({viewport:{width:1100,height:745},deviceScaleFactor:1});
  await page.addInitScript(fixedClock);
  if(process.env.RIDGE_ACTORS)await page.route('**/race-integration/actors.js',r=>r.fulfill({path:process.env.RIDGE_ACTORS,contentType:'text/javascript'}));
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/favicon.ico'))errors.push(r.status()+' '+r.url());});
  try{
    await page.goto(base+'?raceTrial=1&verify=1&field='+field+'&count='+n+'&look='+mode);
    await ready(page,mode==='pixel');
    assert.equal(await page.locator('#race-trial h2').textContent(),'S型レース試験');
    assert.equal(await page.locator('#selected-title').textContent(),'Selected #'+String(Math.min(n,6)).padStart(2,'0'));
    const click=sel=>page.locator(sel).dispatchEvent('click');
    const tick=num=>page.evaluate(n=>tickRace(n),num);
    const checkpoint=async(label,shot=false)=>{
      const data=await page.evaluate(capture=>{
        tickRace();const s=raceSnapshot(), {pixels,...rest}=s;
        const visible=s.runners.map(r=>r.visible);
        const runners=rest.runners.map(({visible,...r})=>r);
        return {state:{...rest,runners},visible,draw:pixels.draw,gl:document.querySelector('#game').getContext('webgl2').getError(),
          png:capture?document.querySelector('#game').toDataURL().split(',')[1]:null};
      },shot);
      assert.equal(data.gl,0);
      assert.equal(data.state.runners.length,n);assert.equal(data.state.order.length,n);
      const hidden=['tactical','lab'].includes(data.state.view);
      for(const [i,r] of data.state.runners.entries()){
        assert.equal(data.visible[i],!hidden&&!(mode==='pixel'&&r.morph==='S'&&label!=='temporary-classic'));
      }
      const mix=data.draw?.mix;
      if(mix){
        assert.equal(Object.values(mix).reduce((a,b)=>a+b),data.state.runners.filter(r=>r.morph==='S').length);
        assert.equal(data.draw.atlasErrors.length,0);
        for(const a of data.draw.details){
          const r=data.state.runners.find(r=>r.id===a.id);
          assert.ok(Math.abs(a.direction[0]-Math.cos(r.yaw))<1e-8&&Math.abs(a.direction[1]+Math.sin(r.yaw))<1e-8);
          assert.equal(a.base[0],r.position[0]);assert.equal(a.base[2],r.position[2]);assert.ok(a.base[1]>=.03&&a.base[1]<.04);
          assert.ok(a.pose>=0&&a.pose<=24&&a.fraction>=0&&a.fraction<1);
        }
      }
      if(data.png&&screenshotFolder)await fs.writeFile(path.join(screenshotFolder,[field,n,mode,label].join('-')+'.png'),Buffer.from(data.png,'base64'));
      return {label,hash:sha(JSON.stringify(data.state)),pixelHash:data.png?sha(Buffer.from(data.png,'base64')):null,
        mix,details:data.draw?.details,elapsed:data.state.elapsed_ms,rank:data.state.rank};
    };
    const checkpoints=[];
    await tick(22);
    if(mode==='pixel')await page.waitForTimeout(350);
    checkpoints.push(await checkpoint('race',true));
    await click('#pause');const at=await page.evaluate(()=>raceSnapshot().elapsed_ms);
    await tick(3);checkpoints.push(await checkpoint('pause'));
    assert.equal(at,checkpoints.at(-1).elapsed);
    await page.selectOption('#trial-mode','classic',{force:true});checkpoints.push(await checkpoint('temporary-classic'));
    await page.selectOption('#trial-mode',mode,{force:true});
    await click('#pause'); await click('[data-view="follow"]');await tick(26);
    if(mode==='pixel')await page.waitForTimeout(300);
    checkpoints.push(await checkpoint('follow',true));
    await click('[data-view="tactical"]');await tick(12);checkpoints.push(await checkpoint('tactical',true));
    await click('[data-view="lab"]');await tick(3);checkpoints.push(await checkpoint('lab'));
    await click('[data-view="race"]');await click('#pause');await click('#reset');
    checkpoints.push(await checkpoint('reset'));assert.equal(checkpoints.at(-1).elapsed,0);
    const {runners}=await page.evaluate(()=>raceSnapshot());
    assert.ok(runners.every((r,i)=>r.speed===0&&r.stamina===100&&r.distance===(n-1-i)*1.1));
    assert.equal(await page.locator('.rank-row').count(),n);
    assert.deepEqual(errors,[]);
    return checkpoints;
  }finally{await page.close();}
}
try{
  for(const [n,field] of [[1,'s'],[10,'s'],[50,'s'],[100,'s'],[18,'mixed']]){
    const classic=await run(n,field,'classic'),pixel=await run(n,field,'pixel');
    for(let i=0;i<classic.length;i++)assert.equal(pixel[i].hash,classic[i].hash,field+' '+n+' '+pixel[i].label);
    const take=(list,k)=>list.find(s=>s.label===k).pixelHash;
    assert.equal(take(pixel,'tactical'),take(classic,'tactical'));
    assert.notEqual(take(pixel,'race'),take(classic,'race'));
    manifest.cases.push({count:n,field,matching_checkpoints:pixel.length,tactical_pixels_equal:true,
      checkpoints:pixel.map(({details,pixelHash,...s})=>s)});
    console.log(n,field,'passed');
  }
  // Follow the ordinary 18-runner engine through MID/FINAL, lane exclusion,
  // blocking and changes of lead. Tactical is the game's inexpensive marker view.
  const page=await browser.newPage({viewport:{width:850,height:640}});
  await page.addInitScript(fixedClock);
  await page.goto(base+'?raceTrial=1&verify=1&count=18&field=mixed&look=classic');
  await ready(page);
  const history=await page.evaluate(()=>{
    document.querySelector('[data-view="tactical"]').click();
    const decisions=new Set(),phases=new Set(),orders=new Set();let changes=0;
    for(let i=0;i<2600;i++){
      tickRace(1,45);
      if(i%12)continue;
      const s=raceSnapshot();orders.add(s.order.join('/'));phases.add(document.querySelector('#phase').textContent);
      for(const r of s.runners){decisions.add(r.decision);if(r.lane!==(r.id-1)%6)changes++;}
    }
    return {decisions:[...decisions],phases:[...phases],orders:orders.size,changed_lane_observations:changes};
  });
  assert.ok(history.orders>1&&history.changed_lane_observations>0);
  assert.ok(history.decisions.includes('BLOCKED')&&history.decisions.includes('OVERTAKE')&&history.phases.includes('FINAL'));
  manifest.race_logic=history;await page.close();
  await fs.writeFile(path.join(evidence,'regression.json'),JSON.stringify(manifest,null,2)+'\n');
}finally{await browser.close();}

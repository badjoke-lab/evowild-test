import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {recordLaneExecution,observeLaneExecution,laneExecutionText} from '../src/race_lane_execution_2p5d.js';
import {resolveRecordedAgentDecision} from '../src/race_agent_outcome_2p5d.js';
import {makeRaceRecord,validateRaceRecord,appendRaceResult,loadGameState,GAME_STORAGE_KEY,ENTRANTS} from '../src/game_progress_2p5d.js';

function rejectedThenEngine(){
  const rejected={at:100,command:'SHIFT_LINE',reason:'Agent request rejected',result:'FAILED'};
  const runner={lane:1,targetLane:1,agent:{decisions:[rejected],commandUntil:2300,lastResult:'FAILED'}};
  recordLaneExecution(runner,{source:'AGENT',at:100,targetLane:3,decision:rejected});
  const engine=recordLaneExecution(runner,{source:'ENGINE',at:200,targetLane:2,reason:'Better forward clearance'});
  runner.targetLane=2;
  runner.lane=1.5;
  observeLaneExecution(engine,runner,400);
  runner.lane=2;
  observeLaneExecution(engine,runner,700);
  resolveRecordedAgentDecision(runner,700);
  return {runner,rejected,engine};
}
function recordFor(runner){
  return makeRaceRecord({id:'lane-log-ui-fixture',finishedAt:Date.UTC(2026,9,25),selectedRunnerId:1,
    results:ENTRANTS.map((r,i)=>({...r,name:r.id===1?'表示検証サンプル':r.name,finishPlace:i+1,finishTime:45000+i*100})),
    agentDecisions:runner.agent.decisions,engineLaneChanges:runner.engineLaneChanges});
}
test('failed Agent request cannot inherit a later engine adjustment success; exact observations survive storage',()=>{
  const {runner,rejected,engine}=rejectedThenEngine();
  expect(rejected).toMatchObject({source:'AGENT',result:'FAILED',fromLane:1,targetLane:3,actualLane:1,observedAt:100});
  expect(engine).toMatchObject({source:'ENGINE',result:'SUCCESS',fromLane:1,targetLane:2,actualLane:runner.lane,observedAt:700});
  const record=recordFor(runner);
  expect(record).not.toBeNull();
  let saved;
  const storage={getItem:()=>saved,setItem:(_key,value)=>saved=value};
  expect(appendRaceResult(storage,record)).toBe(true);
  const restored=loadGameState(storage).history[0];
  expect(restored.agentDecisions[0]).toEqual(rejected);
  expect(restored.engineLaneChanges[0]).toEqual(engine);
  // The saved execution is a snapshot, not a pointer to subsequent movement.
  runner.lane=0;
  expect(restored.engineLaneChanges[0].actualLane).toBe(2);
});
test('ownership replacement cannot credit Agent arrival even when the target lane matches',()=>{
  const decision={at:0,command:'SHIFT_LINE',reason:'Clear traffic',result:'PENDING'};
  const runner={lane:1,targetLane:3,agent:{decisions:[decision],commandUntil:2200}};
  recordLaneExecution(runner,{source:'AGENT',at:0,targetLane:3,decision});
  recordLaneExecution(runner,{source:'ENGINE',at:100,targetLane:3,reason:'Engine takeover'});
  runner.lane=3;
  expect(resolveRecordedAgentDecision(runner,1000)).toBe('FAILED');
  expect(decision.actualLane).toBe(1);
  expect(decision.observedAt).toBe(100);
  expect(observeLaneExecution(runner.engineLaneChanges[0],runner,1000)).toBe('SUCCESS');
});
test('engine movement stays pending while moving and records partial or failed interruptions',()=>{
  for(const [lane,result] of [[1,'FAILED'],[1.5,'PARTIAL']]){
    const runner={lane:1,targetLane:3};
    const event=recordLaneExecution(runner,{source:'ENGINE',at:0,targetLane:3,reason:'Clearance'});
    runner.lane=lane;
    expect(observeLaneExecution(event,runner,400)).toBe('PENDING');
    runner.finished=true;
    expect(observeLaneExecution(event,runner,500)).toBe(result);
    expect(event.actualLane).toBe(lane);
  }
});
test('legacy records still load; forged provenance, lanes and unobserved success are rejected',()=>{
  const {runner}=rejectedThenEngine();
  const record=recordFor(runner);
  const legacy=structuredClone(record);delete legacy.engineLaneChanges;
  legacy.agentDecisions=legacy.agentDecisions.map(({at,command,result,reason})=>({at,command,result,reason}));
  expect(validateRaceRecord(legacy)).toBe(true);
  for(const patch of [{source:'AGENT'},{actualLane:4},{actualLane:1.5},{observedAt:0}]){
    const bad=structuredClone(record);Object.assign(bad.engineLaneChanges[0],patch);
    expect(validateRaceRecord(bad)).toBe(false);
  }
  const bad=structuredClone(record);bad.agentDecisions[0].source='ENGINE';
  expect(validateRaceRecord(bad)).toBe(false);
});

test('saved history separates engine success from rejected Agent request after reload',async({page},testInfo)=>{
  const {runner,rejected,engine}=rejectedThenEngine();
  const state={schemaVersion:1,selectedRunnerId:1,history:[recordFor(runner)]};
  await page.goto('/evowild-test/game-2p5d.html#history',{waitUntil:'networkidle'});
  await page.evaluate(({key,state})=>localStorage.setItem(key,JSON.stringify(state)),{key:GAME_STORAGE_KEY,state});
  await page.reload({waitUntil:'networkidle'});
  for(const source of ['AGENT','ENGINE'])await page.locator(`details[data-source="${source}"] summary`).click();
  for(const [source,event] of [['AGENT',rejected],['ENGINE',engine]]){
    const row=page.locator(`details[data-source="${source}"] li`);
    await expect(row).toContainText(event.result);
    await expect(row).toContainText(laneExecutionText(event));
    expect(JSON.parse(await row.getAttribute('data-lane-execution'))).toEqual(event);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  fs.mkdirSync('test-results/visuals',{recursive:true});
  await page.screenshot({path:`test-results/visuals/lane-history-${testInfo.project.name}.png`,fullPage:true});
});

test('live Agent lane observations match physical movement before and after arrival',async({page},testInfo)=>{
  await page.clock.install();
  await page.goto('/evowild-test/race-stadium.html?laneReview=1&selected=1',{waitUntil:'networkidle'});
  await page.clock.pauseAt(new Date(Date.now()+1000));
  await page.locator('#startAutonomous').click();
  await page.clock.runFor(2600);
  // Follow the issued lane request even if a later HOLD becomes the newest row.
  const row=page.locator('#autoTimeline li[data-command="SHIFT_LINE"]').first();
  const stage=page.locator('#stage');
  await expect(row).toHaveAttribute('data-result','PENDING');
  let event=JSON.parse(await row.getAttribute('data-lane-execution'));
  expect(event.source).toBe('AGENT');
  expect(event.actualLane).toBeCloseTo(Number(await stage.getAttribute('data-selected-lane')),2);
  expect(event.actualLane).not.toBe(event.targetLane);
  await page.clock.runFor(1800);
  await expect(row).toHaveAttribute('data-result','SUCCESS');
  event=JSON.parse(await row.getAttribute('data-lane-execution'));
  expect(event.actualLane).toBe(event.targetLane);
  expect(event.actualLane).toBe(Number(await stage.getAttribute('data-selected-lane')));
  await expect(page.locator('#autoResult')).toHaveText(event.result);
  // Reuse the exact observed live event through the real record/store validator.
  const restored=JSON.parse(JSON.stringify(recordFor({agent:{decisions:[event]},engineLaneChanges:[]})));
  expect(restored.agentDecisions[0]).toEqual(event);
  fs.mkdirSync('test-results/visuals',{recursive:true});
  await page.screenshot({path:`test-results/visuals/lane-live-${testInfo.project.name}.png`,fullPage:true});
});

test('normal race exposes engine movement separately while the earlier Agent request stays failed',async({page},testInfo)=>{
  test.setTimeout(60000);
  await page.clock.install();
  await page.goto('/evowild-test/race-stadium.html?selected=4',{waitUntil:'networkidle'});
  await page.clock.pauseAt(new Date(Date.now()+1000));
  await page.locator('#startAutonomous').click();
  await page.clock.runFor(8000);
  const agentRow=page.locator('#autoTimeline li[data-command="SHIFT_LINE"]').first();
  await expect(agentRow).toHaveAttribute('data-result','FAILED');
  const rejected=JSON.parse(await agentRow.getAttribute('data-lane-execution'));
  await page.locator('#spectatorDetails > summary').click();
  await page.locator('#engineLaneDetails summary').click();
  const engineRow=page.locator('#engineTimeline li').first();
  const moving=JSON.parse(await engineRow.getAttribute('data-lane-execution'));
  expect(moving.source).toBe('ENGINE');
  expect(moving.actualLane).toBeCloseTo(Number(await page.locator('#stage').getAttribute('data-selected-lane')),2);
  // Three lanes at the existing 1.9 lanes/s takes about 1.58s.
  await expect(engineRow).toHaveAttribute('data-result','PENDING');
  await page.clock.runFor(2000);
  await expect(engineRow).toHaveAttribute('data-result','SUCCESS');
  const arrived=JSON.parse(await engineRow.getAttribute('data-lane-execution'));
  expect(arrived.at).toBe(moving.at);
  expect(arrived.actualLane).toBe(arrived.targetLane);
  expect(arrived.actualLane).toBe(Number(await page.locator('#stage').getAttribute('data-selected-lane')));
  const agentEvents=await page.locator('#autoTimeline li[data-lane-execution]').evaluateAll(nodes=>nodes.map(n=>JSON.parse(n.dataset.laneExecution)));
  expect(agentEvents.find(e=>e.at===rejected.at)).toEqual(rejected);
  const saved=recordFor({agent:{decisions:agentEvents},engineLaneChanges:[arrived]});
  expect(saved.agentDecisions.find(e=>e.at===rejected.at)).toEqual(rejected);
  expect(saved.engineLaneChanges[0]).toEqual(arrived);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
  fs.mkdirSync('test-results/visuals',{recursive:true});
  await page.screenshot({path:`test-results/visuals/lane-engine-${testInfo.project.name}.png`,fullPage:true});
});

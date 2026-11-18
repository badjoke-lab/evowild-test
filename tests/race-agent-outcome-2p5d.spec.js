import {test, expect} from '@playwright/test';
import {resolveRecordedAgentDecision} from '../src/race_agent_outcome_2p5d.js';
function moving(){return {lane:1,targetLane:3,finished:false,agent:{commandUntil:2200,lastResult:'PENDING',
  decisions:[{at:0,command:'SHIFT_LINE',result:'PENDING',fromLane:1,targetLane:3}]}};}
test('lane request remains pending until the Creature actually reaches its target',()=>{
  const r=moving();
  expect(resolveRecordedAgentDecision(r,0)).toBe('PENDING');
  r.lane=2;
  expect(resolveRecordedAgentDecision(r,500)).toBe('PENDING');
  r.lane=3;
  expect(resolveRecordedAgentDecision(r,1100)).toBe('SUCCESS');
  expect(r.agent.lastResult).toBe('SUCCESS');
  expect(r.agent.decisions[0].result).toBe('SUCCESS');
});
test('interrupted, expired or finish-cutoff lane changes cannot be recorded as success',()=>{
  const stopped=moving();
  stopped.targetLane=1;
  expect(resolveRecordedAgentDecision(stopped,100)).toBe('FAILED');
  const partial=moving();partial.lane=2;partial.finished=true;
  expect(resolveRecordedAgentDecision(partial,1000)).toBe('PARTIAL');
  const expired=moving();
  expect(resolveRecordedAgentDecision(expired,2200)).toBe('FAILED');
});
test('recorded effort results retain the actual Creature resolver grade',()=>{
  for(const [resolved,expected] of [['STRONG','SUCCESS'],['SETTLED','SUCCESS'],['PARTIAL','PARTIAL'],['WEAK','FAILED'],['EXPIRED','FAILED']]){
    const r={agent:{lastResult:resolved,decisions:[{command:'PUSH',result:'PENDING'}]}};
    expect(resolveRecordedAgentDecision(r,100)).toBe(expected);
    r.agent.lastResult='STRONG';
    expect(resolveRecordedAgentDecision(r,200)).toBe(expected);
  }
});

test('spectator HUD shows execution results alongside each autonomous decision',async ({page})=>{
  await page.goto('/evowild-test/race-stadium.html?selected=4',{waitUntil:'networkidle'});
  await page.locator('#startAutonomous').click();
  await expect(page.locator('#stage')).toHaveAttribute('data-race-state','running',{timeout:12000});
  const latest=page.locator('#autoTimeline li').first();
  await expect(latest).toHaveAttribute('data-result',/SUCCESS|PARTIAL|FAILED/);
  await page.locator('#pause').click();
  const result=await latest.getAttribute('data-result');
  await expect(latest).toContainText(result);
  await expect(page.locator('#autoResult')).toHaveText(result);
});

test('live lane-change feedback waits for arrival before showing SUCCESS',async ({page})=>{
  await page.clock.install();
  await page.goto('/evowild-test/race-stadium.html?laneReview=1&selected=1',{waitUntil:'networkidle'});
  await page.clock.pauseAt(new Date(Date.now()+1000));
  await page.locator('#startAutonomous').click();
  await page.clock.runFor(2600);
  const latest=page.locator('#autoTimeline li').first();
  await expect(latest).toHaveAttribute('data-command','SHIFT_LINE');
  await expect(latest).toHaveAttribute('data-result','PENDING');
  const stage=page.locator('#stage');
  const target=Number(await stage.getAttribute('data-selected-target-lane'));
  expect(Number(await stage.getAttribute('data-selected-lane'))).not.toBe(target);
  await page.clock.runFor(1800);
  await expect(latest).toHaveAttribute('data-result','SUCCESS');
  expect(Number(await stage.getAttribute('data-selected-lane'))).toBe(target);
  await expect(page.locator('#autoResult')).toHaveText('SUCCESS');
});

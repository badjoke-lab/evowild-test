import {test, expect} from '@playwright/test';
import fs from 'node:fs';
import {GAME_STORAGE_KEY, validateRaceRecord, formatRaceTime} from '../src/game_progress_2p5d.js';
import {makeAgentFile} from '../src/race_agent_v1.js';

const home='/evowild-test/game-2p5d.html';
const race='/evowild-test/race-stadium.html';
const stored=page=>page.evaluate(key=>JSON.parse(localStorage.getItem(key)),GAME_STORAGE_KEY);
const screenshot=async (page,testInfo,name)=>{
  fs.mkdirSync('test-results/visuals',{recursive:true});
  await page.screenshot({path:`test-results/visuals/loop-${name}-${testInfo.project.name}.png`,fullPage:true});
};

test('real complete journey saves exactly one 18-runner result and survives reload',async ({page},testInfo)=>{
  test.setTimeout(180000);
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(home,{waitUntil:'networkidle'});
  await page.locator('[data-nav="course"]').click();
  await expect(page.locator('.course-card')).toHaveCount(1);
  await page.locator('[data-nav="creatures"]').click();
  await page.locator('[data-runner-id="4"]').click();
  await page.locator('#saveCreature').click();
  await page.locator('#playFromCreatures').click();
  await expect(page.locator('#entryRunnerSelect')).toHaveValue('4');
  await expect(page.locator('[data-agent-field]')).toHaveCount(7);
  await page.locator('#presetSelect').selectOption('CLOSER');
  await screenshot(page,testInfo,'setup');
  await page.locator('#startAutonomous').click();
  const stage=page.locator('#stage');
  await expect(stage).toHaveAttribute('data-race-state','running',{timeout:12000});
  await expect(page.locator('button[data-agent-command], [role="button"][data-agent-command]')).toHaveCount(0);
  await expect(stage).toHaveAttribute('data-agent-auto-all','18');
  await expect.poll(async()=>Number(await stage.getAttribute('data-selected-distance')),{timeout:20000}).toBeGreaterThan(120);
  await page.locator('#pause').click();
  const pausedDistance=await stage.getAttribute('data-selected-distance');
  await page.waitForTimeout(250);
  await expect(stage).toHaveAttribute('data-selected-distance',pausedDistance);
  expect((await stored(page)).history).toHaveLength(0);
  const orbCount=Number(await stage.getAttribute('data-orb-count'));
  expect(orbCount).toBeGreaterThan(0);
  expect(orbCount).toBe(Number(await stage.getAttribute('data-visible-racers')));
  await screenshot(page,testInfo,'race');
  await page.locator('#pause').click();
  // No finishReview, state injection or simulated finish: let all 18 run 1600m.
  await expect(stage).toHaveAttribute('data-race-state','finished',{timeout:120000});
  await expect(stage).toHaveAttribute('data-record-saved','1');
  const rows=page.locator('#resultList li');
  await expect(rows).toHaveCount(18);
  const state=await stored(page);
  expect(state.history).toHaveLength(1);
  const record=state.history[0];
  expect(validateRaceRecord(record)).toBe(true);
  expect(record.playerRunnerId).toBe(4);
  expect(record.agentFile).toEqual(makeAgentFile('CLOSER'));
  expect(record.agentDecisions.length).toBeGreaterThan(0);
  expect(record.agentDecisions.every(d=>d.result!=='PENDING')).toBe(true);
  const screenResults=await rows.evaluateAll(nodes=>nodes.map(n=>({id:Number(n.dataset.runnerId),time:Number(n.dataset.finishTime)})));
  const ranked=[...record.results].sort((a,b)=>a.place-b.place);
  expect(screenResults.map(r=>r.id)).toEqual(ranked.map(r=>r.id));
  for(let i=0;i<18;i++){
    expect(screenResults[i].time).toBeCloseTo(ranked[i].timeMs,0);
    if(i>0)expect(ranked[i].timeMs).toBeGreaterThanOrEqual(ranked[i-1].timeMs);
  }
  await screenshot(page,testInfo,'results');
  await page.locator('#goToHistory').click();
  await page.reload({waitUntil:'networkidle'});
  await expect(page.locator('.history-card')).toHaveCount(1);
  await page.locator('.history-details summary').click();
  await expect(page.locator('.race-places li')).toHaveCount(18);
  await expect(page.locator('.race-places li').first()).toContainText(formatRaceTime(ranked[0].timeMs));
  // Agent decisions and engine-initiated lane adjustments are separate logs.
  // Scope each disclosure explicitly, rather than matching both with one click.
  const agentHistory=page.locator('.agent-history-details[data-source="AGENT"]');
  const engineHistory=page.locator('.agent-history-details[data-source="ENGINE"]');
  await expect(agentHistory).toHaveCount(1);
  await expect(engineHistory).toHaveCount(1);
  await agentHistory.locator('summary').click();
  await engineHistory.locator('summary').click();
  await expect(agentHistory.locator('.agent-history-row')).toHaveCount(record.agentDecisions.length);
  await expect(engineHistory.locator('.agent-history-row')).toHaveCount(record.engineLaneChanges.length);
  await screenshot(page,testInfo,'history');
  expect((await stored(page)).history).toEqual([record]);
  await page.reload({waitUntil:'networkidle'});
  expect((await stored(page)).history).toEqual([record]);
  expect(errors).toEqual([]);
});

test('Agent File export/import roundtrip rejects malformed, privileged and oversized files',async ({page})=>{
  await page.goto(race+'?selected=4',{waitUntil:'networkidle'});
  await page.locator('#presetSelect').selectOption('CLOSER');
  const downloadPromise=page.waitForEvent('download');
  await page.locator('#exportAgent').click();
  const download=await downloadPromise;
  const raw=fs.readFileSync(await download.path(),'utf8');
  expect(JSON.parse(raw)).toEqual(makeAgentFile('CLOSER'));
  for(const bad of ['{',JSON.stringify({...makeAgentFile(),privilegedLiveAI:true}),' '.repeat(16385)]){
    await page.locator('#importAgent').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(bad)});
    await expect(page.locator('#setupValidation')).toContainText('読み込み不可');
    await expect(page.locator('[name="basePace"]')).toHaveValue('CONSERVE');
  }
  await page.locator('#presetSelect').selectOption('FRONT');
  await page.locator('#importAgent').setInputFiles({name:'roundtrip.json',mimeType:'application/json',buffer:Buffer.from(raw)});
  await expect(page.locator('#setupValidation')).toContainText('読み込みました');
  await expect(page.locator('#presetSelect')).toHaveValue('CLOSER');
  await page.locator('#startAutonomous').click();
  await page.reload({waitUntil:'networkidle'});
  await expect(page.locator('#presetSelect')).toHaveValue('CLOSER');
  expect((await stored(page)).history).toHaveLength(0);
});

test('reset and navigation during an unfinished race never create a history record',async ({page})=>{
  await page.goto(race+'?selected=4',{waitUntil:'networkidle'});
  await page.locator('#startAutonomous').click();
  await expect(page.locator('#stage')).toHaveAttribute('data-race-state','running',{timeout:12000});
  await page.locator('#reset').click();
  await expect(page.locator('#preRacePanel')).toBeVisible();
  expect((await stored(page)).history).toHaveLength(0);
  await page.locator('#startAutonomous').click();
  await expect(page.locator('#stage')).toHaveAttribute('data-race-state','running',{timeout:12000});
  await page.locator('.game-home-link').click();
  await page.locator('[data-nav="history"]').click();
  await expect(page.locator('#historyEmpty')).toBeVisible();
  await page.reload({waitUntil:'networkidle'});
  expect((await stored(page)).history).toHaveLength(0);
});

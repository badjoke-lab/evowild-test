import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {GAME_STORAGE_KEY} from '../src/game_progress_2p5d.js';
import {historyLayoutFixture} from './fixtures/agent-history.js';

test('Agent history separates readable values and wraps long reasons without horizontal overflow',async ({page},testInfo)=>{
  const fixture=historyLayoutFixture();
  await page.goto('/evowild-test/game-2p5d.html#history',{waitUntil:'networkidle'});
  await page.evaluate(({key,state})=>localStorage.setItem(key,JSON.stringify(state)),{key:GAME_STORAGE_KEY,state:fixture});
  await page.reload({waitUntil:'networkidle'});
  await page.locator('.agent-history-details summary').click();
  await expect(page.locator('.history-card h2')).toContainText('表示検証サンプル');
  fs.mkdirSync('test-results/visuals',{recursive:true});
  await page.screenshot({path:`test-results/visuals/history-layout-${testInfo.project.name}.png`,fullPage:true});
  const checkLayout=async()=>{
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);
    const rows=page.locator('.agent-history-list li');
    await expect(rows).toHaveCount(3);
    for(const row of await rows.all()){
      for(const label of ['時刻','指令','実行結果','理由'])await expect(row.getByText(label,{exact:true})).toBeVisible();
      const boxes=await row.locator('dd').evaluateAll(nodes=>nodes.map(n=>{
        const b=n.getBoundingClientRect();return {x:b.x,y:b.y,right:b.right,bottom:b.bottom};
      }));
      for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
        const a=boxes[i],b=boxes[j];
        expect(a.right<=b.x || b.right<=a.x || a.bottom<=b.y || b.bottom<=a.y).toBe(true);
      }
    }
  };
  await checkLayout();
  if(testInfo.project.name==='android-chromium'){
    await page.setViewportSize({width:320,height:740});
    await checkLayout();
  }
  // Rendering the archive must not rewrite its persisted records.
  expect(await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),GAME_STORAGE_KEY)).toEqual(fixture);
});

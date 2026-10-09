import {test,expect} from '@playwright/test';
import fs from 'node:fs/promises';
const target='/evowild-test/preview-motion-first-race/index.html?skipStart=1';

test.beforeEach(async({page,baseURL})=>{
  await page.route('**/*',route=>new URL(route.request().url()).origin===new URL(baseURL).origin ? route.continue() : route.abort());
});
async function boot(page,url=target){
  await page.goto(url);
  await expect(page.locator('#scene')).toHaveAttribute('data-runner-count','18');
  await expect(page.locator('#loading')).toBeHidden();
}
test('Game Studio 3D boots offline with 18 articulated proxies and unchanged color buffers',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const probe=await fs.readFile('scripts/gamestudio-3d/probe.js','utf8');
  await page.route('**/preview-motion-first/main.js',async route=>{const response=await route.fetch();await route.fulfill({response,body:(await response.text())+'\n'+probe+'\nwindow.__recolorForTest = () => runners[0].raceProxy.userData.raceProxy.colors.dark.set(0xffffff);'});});
  await boot(page);await page.waitForTimeout(1500);
  const a=await page.evaluate(()=>window.__gameStudioProbe());
  await page.waitForTimeout(1100);
  const b=await page.evaluate(()=>window.__gameStudioProbe());
  expect(errors).toEqual([]);
  expect(new Set(b.runners.map(r=>r.morph))).toEqual(new Set(['S','P','E','A']));
  expect(b.dataset.raceProxyInstanceCount).toBe('18');
  expect(b.dataset.raceProxyUpdateMode).toBe('canonical-direct');
  expect(b.colorVersions).toEqual(a.colorVersions);
  expect(b.colors).toEqual(a.colors);
  expect(b.raceTime).toBeGreaterThan(a.raceTime);
  expect(b.calls).toBeLessThanOrEqual(32);
  await page.evaluate(()=>window.__recolorForTest());
  await page.waitForTimeout(300);
  const changed=await page.evaluate(()=>window.__gameStudioProbe());
  expect(changed.colorVersions.foot).toBeGreaterThan(b.colorVersions.foot);
  expect(changed.colors.foot).not.toEqual(b.colors.foot);
});

test('Game Studio 3D typing and native controls do not trigger global shortcuts',async({page})=>{
  await boot(page);
  await page.locator('#agentPanel').evaluate(e=>e.open=true);
  await page.locator('#agentDetails > summary').click();
  await page.locator('[data-camera="FRONT"]').click();
  const input=page.locator('#agentOwnerInput');await input.fill('PLAYER');
  await input.press('Space');await input.press('Digit2');
  await expect(input).toHaveValue('PLAYER 2');
  await expect(page.locator('#pauseButton')).toHaveText('PAUSE');
  await expect(page.locator('#cameraReadout')).toHaveText('FRONT');
  await page.locator('#pauseButton').focus();await page.keyboard.press('Space');
  await expect(page.locator('#pauseButton')).toHaveText('RESUME');
  await page.locator('#pauseButton').press('Space');
  await expect(page.locator('#pauseButton')).toHaveText('PAUSE');
  await page.locator('#pauseButton').evaluate(e=>e.blur());
  await page.keyboard.press('Space');await expect(page.locator('#pauseButton')).toHaveText('RESUME');
  await page.keyboard.down('Space');await page.keyboard.down('Space');await page.keyboard.up('Space');
  await expect(page.locator('#pauseButton')).toHaveText('PAUSE');
});

test('Game Studio 3D manual views retain focus and fit touch controls',async({page},info)=>{
  await boot(page);
  for(const camera of ['SIDE','LOW','CHASE','FRONT']){
    const button=page.locator(`[data-camera="${camera}"]`);
    const box=await button.boundingBox();const viewport=page.viewportSize();
    expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(viewport.width);
    if(info.project.name==='android-chromium')expect(box.height).toBeGreaterThanOrEqual(44);
    await button.click();await page.selectOption('#runnerSelect','8');await page.waitForTimeout(300);
    await expect(page.locator('#cameraReadout')).toHaveText(camera);
    await expect(page.locator('#runnerName')).toContainText('Runner 09');
  }
  await page.locator('#pauseButton').click();
  const distance=await page.locator('#distanceReadout').textContent();await page.waitForTimeout(350);
  await expect(page.locator('#distanceReadout')).toHaveText(distance);
  await page.locator('#restartButton').click();await expect(page.locator('#pauseButton')).toHaveText('PAUSE');
});

test('Game Studio 3D secondary panels remain reachable without covering the race by default',async({page},info)=>{
  await boot(page);
  await expect(page.locator('#agentOwnerInput')).toBeHidden();
  if(info.project.name==='android-chromium'){
    await expect(page.locator('#courseSelect')).toBeHidden();
    await expect(page.locator('#agentTargetSelect')).toBeHidden();
    await page.locator('#raceSetup > summary').click();
  }
  await expect(page.locator('#courseSelect')).toBeVisible();
  await expect(page.locator('#entryCreatureSelect option')).toHaveCount(18);
  if(info.project.name==='android-chromium')await page.locator('#raceSetup > summary').click();
  await page.locator('#agentPanel').evaluate(e=>e.open=true);
  await page.locator('[data-agent-command="PUSH"]').click();
  await expect(page.locator('#agentResult')).not.toHaveText('No active command');
  await page.locator('#agentDetails > summary').click();
  await expect(page.locator('#agentOwnerInput')).toBeVisible();
  if(info.project.name==='android-chromium'){
    await page.setViewportSize({width:1280,height:720});
    await page.locator('#raceSetup > summary').click();
    await expect(page.locator('#courseSelect')).toBeVisible();
  }
});

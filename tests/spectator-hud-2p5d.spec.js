import {test,expect} from '@playwright/test';
import {prepareSpectator,captureSpectator} from './helpers/spectator-capture.js';

test('compact spectator HUD leaves selected Creature and orb clear through start, turn, pack and straight',async({page},testInfo)=>{
  test.setTimeout(120000);
  await prepareSpectator(page);
  const details=page.locator('#spectatorDetails');
  await expect(details).not.toHaveAttribute('open','');
  const frames=await captureSpectator(page,`test-results/visuals/spectator-${testInfo.project.name}`);
  expect(frames.map(f=>f.segment)).toEqual(['HOME_STRAIGHT','FIRST_TURN','FIRST_TURN','BACK_STRAIGHT']);
  for(const frame of frames){
    expect(frame.orbs).toBe(frame.visibleRacers);
    expect(frame.visibleRacers).toBeGreaterThanOrEqual(14);
    expect(frame.hud.height).toBeLessThan(135);
    for(const point of [frame.creature,frame.orb]){
      expect(point.x).toBeGreaterThan(0);expect(point.x).toBeLessThan(frame.viewport.width);
      expect(point.y).toBeGreaterThan(0);expect(point.y).toBeLessThan(frame.viewport.height);
      const b=frame.hud;
      expect(point.x<b.x||point.x>b.x+b.width||point.y<b.y||point.y>b.y+b.height).toBe(true);
    }
  }
  await expect(page.locator('#autoCreatureName')).toHaveText('#04 Serein · A');
  for(const selector of ['#rank','#autoFatigue','#autoCommand','#autoResult'])await expect(page.locator(selector)).toBeVisible();
  for(const selector of ['#autoReason','#autoTimeline','#command','#ranking'])await expect(page.locator(selector)).toBeHidden();
  const stage=page.locator('#stage');
  const distance=await stage.getAttribute('data-selected-distance');
  // Opening information does not issue commands or alter the paused-clock simulation.
  await details.locator(':scope > summary').click();
  await expect(page.locator('#autoTimeline li').first()).toBeVisible();
  await expect(page.locator('#command')).toBeVisible();
  await expect(page.locator('#ranking span')).toHaveCount(18);
  expect(await stage.getAttribute('data-selected-distance')).toBe(distance);
  await details.locator(':scope > summary').focus();
  await page.keyboard.press('Escape');
  await expect(page.locator('#autoTimeline')).toBeHidden();
  await expect(details.locator(':scope > summary')).toBeFocused();
  await page.setViewportSize({width:320,height:740});
  await expect(page.locator('#autoCreatureName')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await details.locator(':scope > summary').click();
  await page.locator('#reset').click();
  await expect(stage).toHaveAttribute('data-race-state','setup');
  await expect(details).not.toHaveAttribute('open','');
  await expect(page.locator('#preRacePanel')).toBeVisible();
});

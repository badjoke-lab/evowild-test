// Full course frames, including the original camera's traversal of the LOD
// boundary when the player changes from Race to Follow.
import fs from 'node:fs/promises';
import path from 'node:path';
import {base,evidence,launch,fixedClock,ready} from './browser.mjs';
const dir=process.argv[2];
if(!dir)throw Error('Provide a capture directory');
await fs.mkdir(dir,{recursive:true});
const browser=await launch();
try{
  const page=await browser.newPage({viewport:{width:1100,height:745}});
  await page.addInitScript(fixedClock);
  await page.goto(base+'?raceTrial=1&verify=1&field=s&count=1');
  await ready(page,true);
  await page.evaluate(()=>tickRace(65));
  await page.waitForTimeout(1200);
  // Follow camera eases in at its normal rate; no direct camera controls.
  await page.locator('[data-view="tactical"]').dispatchEvent('click');
  await page.evaluate(()=>tickRace(48));
  await page.locator('[data-view="race"]').dispatchEvent('click');
  const rows=[];
  for(let i=0;i<140;i++){
    if(i===68)await page.locator('[data-view="follow"]').dispatchEvent('click');
    const value=await page.evaluate(()=>{
      tickRace();
      const s=raceSnapshot(),a=s.pixels.draw.details[0],r=s.runners[0],c=document.querySelector('#game');
      return {camera:s.view,game_ms:s.elapsed_ms,actor:a,yaw:r.yaw,speed:r.speed,pending:s.pixels.draw.atlasPending,
        width:c.width,height:c.height,png:c.toDataURL().split(',')[1]};
    });
    const {png,...row}=value;rows.push(row);
    if(row.pending)await page.waitForTimeout(120);
    await fs.writeFile(path.join(dir,'frame-'+i+'.png'),Buffer.from(png,'base64'));
  }
  console.log([...new Set(rows.map(r=>r.actor?.lod))],Math.min(...rows.filter(r=>r.actor).map(r=>r.actor.span)));
  if(!rows.some(r=>r.actor?.lod==='transition'&&!r.pending)||!rows.some(r=>r.actor?.lod==='sprite')||!rows.some(r=>['race','fine'].includes(r.actor?.lod)))throw Error('LOD sweep missing states');
  await fs.writeFile(path.join(evidence,'quality-frames.json'),JSON.stringify(rows)+'\n');
}finally{await browser.close();}

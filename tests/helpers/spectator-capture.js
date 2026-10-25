import fs from 'node:fs';
export const spectatorPhases=[['start',2600],['corner',3400],['pack',4000],['straight',9000]];
export async function prepareSpectator(page){
  await page.clock.install();
  await page.goto('/evowild-test/race-stadium.html?selected=4',{waitUntil:'networkidle'});
  await page.clock.pauseAt(new Date(Date.now()+1000));
  await page.locator('#startAutonomous').click();
}
export async function captureSpectator(page,path){
  fs.mkdirSync(path,{recursive:true});
  const frames=[];
  for(const [phase,advance] of spectatorPhases){
    await page.clock.runFor(advance);
    const metrics=await page.locator('#stage').evaluate(stage=>{
      const d=stage.dataset;
      const rect=el=>{const b=el.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height};};
      const hud=document.querySelector('#autoAgentPanel');
      return {viewport:{width:innerWidth,height:innerHeight},segment:d.trackSegment,
        distance:d.selectedDistance,lane:d.selectedLane,speed:d.selectedSpeed,rank:d.selectedRank,
        creature:{x:Number(d.selectedX),y:Number(d.selectedY)},
        orb:{x:Number(d.selectedOrbX),y:Number(d.selectedOrbY)},
        visibleRacers:Number(d.visibleRacers),orbs:Number(d.orbCount),hud:rect(hud)};
    });
    frames.push({phase,...metrics});
    await page.screenshot({path:`${path}/${phase}.png`});
  }
  fs.writeFileSync(`${path}/observations.json`,JSON.stringify(frames,null,2)+'\n');
  return frames;
}

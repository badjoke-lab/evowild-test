import { chromium } from 'playwright';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const root=fileURLToPath(new URL('../../',import.meta.url));
export const evidence=process.env.TRIAL_EVIDENCE||path.join(root,'public/race-integration/evidence');
export const base=process.env.TRIAL_URL||'http://127.0.0.1:4180/evowild-test/';
export function launch(){
  return chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
}
// Deliver fixed frame timestamps through Three.js's real animation loop.
// This lives only in the Playwright process. No test clock ships in the game.
export function fixedClock(){
  let now=1000, serial=0, next=new Map();
  Object.defineProperty(performance,'now',{value:()=>now});
  window.requestAnimationFrame=fn=>{next.set(++serial,fn);return serial;};
  window.cancelAnimationFrame=id=>next.delete(id);
  window.tickRace=(n=1,dt=1000/30)=>{
    for(let i=0;i<n;i++){
      now+=dt;const calls=next;next=new Map();
      for(const callback of calls.values())callback(now);
    }
  };
}
export async function ready(page, pixel=false){
  await page.waitForFunction(want=>typeof window.raceSnapshot==='function'&&(!want||raceSnapshot().pixels.ready||raceSnapshot().pixels.error),pixel,{polling:100});
  const error=await page.evaluate(()=>raceSnapshot().pixels.error);
  if(error)throw Error(error);
}

import {chromium} from 'playwright';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
export const ROOT=fileURLToPath(new URL('../../',import.meta.url));
export const DEMO=path.join(ROOT,'public/s-pixel-lab');
export async function openLab(viewport={width:1280,height:860},mobile=false){
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport,deviceScaleFactor:1,isMobile:mobile,hasTouch:mobile});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto(process.env.LAB_URL||'http://127.0.0.1:4173/s-pixel-lab/');
 try{await page.waitForFunction(()=>!!window.sLab,null,{timeout:90000});}
 catch(e){console.error(errors,await page.locator('#loading').textContent());await browser.close();throw e;}
 return {browser,page,errors};
}

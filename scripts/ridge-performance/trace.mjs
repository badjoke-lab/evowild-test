// Record Chromium's scheduler/renderer trace during a separate unmodified
// 100-S Follow trial. Frame marks link browser tasks to the observed RAF gaps.
import fs from 'node:fs/promises';
import {once} from 'node:events';
import {launch} from '../race-integration/browser.mjs';
const [base,file]=process.argv.slice(2);
const browser=await launch();
try{
 const page=await browser.newPage({viewport:{width:1100,height:745},deviceScaleFactor:1});
 await page.goto(base+'?raceTrial=1&count=100&field=s&look=pixel');
 await page.waitForFunction(()=>document.querySelector('#race-trial').dataset.renderer==='pixel');
 await page.locator('[data-view="follow"]').click();
 await page.getByText('実機計測',{exact:true}).click();
 const client=await page.context().newCDPSession(page);
 await client.send('Tracing.start',{categories:'devtools.timeline,blink.user_timing,gpu',transferMode:'ReturnAsStream'});
 await page.evaluate(async()=>{
   await new Promise(resolve=>{
     let i=0;
     function mark(){
       performance.mark('ridgeFollowFrame'+String(++i).padStart(3,'0'));
       if(i<121)requestAnimationFrame(mark);else resolve();
     }
     document.querySelector('#trial-measure').click();requestAnimationFrame(mark);
   });
 });
 const complete=once(client,'Tracing.tracingComplete');await client.send('Tracing.end');
 const [{stream}]=await complete, dest=await fs.open(file,'w');
 try{
   let end=false;
   while(!end){
     const chunk=await client.send('IO.read',{handle:stream});
     await dest.writeFile(chunk.base64Encoded?Buffer.from(chunk.data,'base64'):chunk.data);end=chunk.eof;
   }
 }finally{await dest.close();await client.send('IO.close',{handle:stream});}
}finally{await browser.close();}

// Produce the public matched-comparison CSV from the two raw captures. Refuse
// to pair a changed camera path, resolution or software GPU with an old row.
import fs from 'node:fs/promises';
import path from 'node:path';
import {DEMO} from '../browser.mjs';
import {RACES} from '../../../public/s-pixel-lab/v3/scenarios.js';
const versions=process.argv[2]==='v4'?['v3','v4']:['v2','v3'];
const dir=path.join(DEMO,versions[1],'evidence');
const [v2,v3]=await Promise.all(versions.map(async name=>JSON.parse(await fs.readFile(path.join(dir,name+'-race.json'),'utf8'))));
for(const key of ['chromium','renderer','dpr','animation_seconds','samples','sync_readback','warmup','scenario']){
 if(v2.environment[key]!==v3.environment[key])throw Error('Unmatched environment: '+key);
}
if(v2.rows.length!==10 || v3.rows.length!==10)throw Error('Expected all five scenarios on both profiles');
const csv=[];
for(const profile of ['desktop','mobile'])for(const key of Object.keys(RACES)){
 const rows=[v2,v3].map(doc=>doc.rows.find(row=>row.profile===profile&&row.scenario===key));
 if(!rows[0]||!rows[1])throw Error('Missing rows for '+profile+'/'+key);
 for(const field of ['width','height','number','frames','cpu','method']){
  if(rows[0][field]!==rows[1][field])throw Error('Unmatched '+field);
 }
 for(let i=0;i<rows[0].frames;i++){
  if(JSON.stringify(rows[0].samples[i].camera)!==JSON.stringify(rows[1].samples[i].camera))throw Error('Unmatched camera or gait at sample '+i);
  if(JSON.stringify(rows[0].samples[i].visible)!==JSON.stringify(rows[1].samples[i].visible))throw Error('Unmatched visibility at sample '+i);
  if(versions[1]==='v4' && JSON.stringify(rows[0].samples[i].mix)!==JSON.stringify(rows[1].samples[i].mix))throw Error('Unmatched LOD distribution at sample '+i);
 }
 for(let i=0;i<2;i++){
  const r=rows[i],m=r.memory;
  const row={version:versions[i],profile:r.profile,scenario:r.scenario,number:r.number,draw_width:r.width,draw_height:r.height,samples:r.frames,
   avg_fps:r.fps,p95_frame_ms:r.p95_ms,gpu_ms:r.gpu_ms,gpu_samples:r.gpu_samples,submit_ms:r.submit_ms,draw_sync_ms:r.draw_sync_ms,
   tris_mean:r.triangles.mean,tris_min:r.triangles.min,tris_max:r.triangles.max,draws_mean:r.draw_calls.mean,blits_mean:r.blits.mean,
   gl_mib:m.gl_mib.toFixed(2),js_heap_mib:m.js_heap_mib.toFixed(2),rss_mib:m.rss_mib?.toFixed(2)??'',
   near_mean:r.mix.near.mean,mid_mean:r.mix.mid?.mean??0,transition_mean:r.mix.transition.mean,sprite_mean:r.mix.sprite.mean,
   offscreen_mean:r.mix.offscreen.mean,visible_body_centres_mean:r.visibility.centre.mean,wholly_inside_bounds_mean:r.visibility.whole.mean};
  if(!csv.length)csv.push(Object.keys(row));csv.push(Object.values(row));
 }
}
await fs.writeFile(path.join(dir,'race-performance.csv'),csv.map(row=>row.join(',')).join('\n')+'\n');

// Supplemental single-variable measurements, each in its own browser process.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {ROOT,DEMO} from '../browser.mjs';
const jobs=[
 ['all-faces','lod','mixed100',48,{frontFaces:false}],
 ['facing','lod','mixed100',48,{}],
 ['hero-0','lod','near1',32,{heroAA:0}],['hero-2','lod','near1',32,{heroAA:2}],['hero-4','lod','near1',32,{heroAA:4}],
 ['ray-1','exact','near1',24,{}],['ray-10','exact','near10',24,{}]
];
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'s03-variants-')),rows=[];
try{
 for(const [id,method,scenario,frames,options] of jobs){
  const file=path.join(temp,id+'.json');const result=spawnSync(process.execPath,[path.join(ROOT,'scripts/s-pixel/v3/measure.mjs'),'v3'],{stdio:'inherit',env:{...process.env,MEASURE_METHOD:method,MEASURE_PROFILE:'desktop',MEASURE_RACE:scenario,MEASURE_FRAMES:String(frames),MEASURE_OPTIONS:JSON.stringify(options),MEASURE_OUT:file}});
  if(result.status!==0)throw Error('Measurement failed: '+id);
  const {samples,...metrics}=JSON.parse(await fs.readFile(file,'utf8')).rows[0];rows.push({id,options,...metrics});
 }
 await fs.writeFile(path.join(DEMO,'v3/evidence/variants.json'),JSON.stringify(rows,null,1)+'\n');
}finally{await fs.rm(temp,{recursive:true,force:true});}

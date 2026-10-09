import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const base='610d42800180ed31f174a097fc2eb96c27ecd0ab';
const file='public/preview-motion-first/main.js';
const before=execFileSync('git',['show',`${base}:${file}`],{encoding:'utf8'});
const after=await fs.readFile(file,'utf8');
const hash=s=>createHash('sha256').update(s).digest('hex');
const ranges=[
  ['designs and race profiles','const S_GAIT =','let simplifiedRaceProxyPool ='],
  ['articulated proxy and canonical pose adapter','function createSimplifiedRaceProxy(', 'function setProxyInstance('],
  ['race state, simulation and gait','function updateSimplifiedRaceLodSelection(', 'function rankings('],
  ['camera and director','function rankings(', 'function updateHud(']
];
const source=[];
for(const [name,start,end] of ranges){
  const extract=s=>{const a=s.indexOf(start),b=s.indexOf(end,a);assert(a>=0&&b>a);return s.slice(a,b);};
  const a=hash(extract(before)),b=hash(extract(after));assert.equal(a,b,name);source.push({name,sha256:a,unchanged:true});
}
const paths=execFileSync('git',['ls-tree','-r','--name-only',base,'public/models','public/concept','docs/references'],{encoding:'utf8'}).trim().split('\n');
for(const p of paths){const original=execFileSync('git',['show',`${base}:${p}`],{maxBuffer:2**25});assert.equal(hash(await fs.readFile(p)),hash(original),p);}
console.log(JSON.stringify({base,source,protectedAssetsChecked:paths.length,unchanged:true},null,2));

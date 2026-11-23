// Alternate order so one version does not always run with a colder host.
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {DEMO,ROOT} from '../browser.mjs';
const out=path.join(DEMO,'v4.1/evidence');
for(let round=1;round<=3;round++){
 const order=round===2?['v4.1','v4']:['v4','v4.1'];
 for(const version of order)execFileSync(process.execPath,['scripts/s-pixel/v3/measure.mjs',version],{cwd:ROOT,stdio:'inherit',env:{...process.env,
  MEASURE_RACE:'mixed50,mixed100',MEASURE_PROFILE:'',MEASURE_FRAMES:'48',MEASURE_METHOD:'lod',MEASURE_OPTIONS:'{}',
  MEASURE_OUT:path.join(out,version+'-round'+round+'.json')}});
}
for(const version of ['v4','v4.1'])execFileSync(process.execPath,['scripts/s-pixel/v4/profile.mjs',version],{cwd:ROOT,stdio:'inherit',env:{...process.env,PASS_OUT_DIR:out}});

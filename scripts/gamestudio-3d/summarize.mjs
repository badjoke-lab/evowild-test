import fs from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
const root='docs/evidence/gamestudio-3d-20261010';
const percentile=(a,p)=>a.length?[...a].sort((a,b)=>a-b)[Math.min(a.length-1,Math.floor(a.length*p))]:null;
const mean=a=>a.reduce((s,n)=>s+n,0)/a.length;
const summary={method:'FPS uses wall-clock RAF intervals with video and identical read-only probe enabled. Foot clearance is min transformed foot/toe bounding-box Y above TRACK Y=0, not the grass plane at -0.12. Original samples relative to the grass plane are rebased using referenceSurfaceY. Stance drift is horizontal displacement from first sampled rendered foot center within the same stance cycle; every-render-frame supplemental samples still yield a LOWER BOUND, not full contact validation. Video times are approximate (page performance clock). No claim of physical Android performance.',runs:{}};
for(const phase of ['before','after'])for(const device of ['desktop','android']){
  const raw=JSON.parse(gunzipSync(await fs.readFile(`${root}/${phase}/${device}/raw.json.gz`)));
  const contact=JSON.parse(gunzipSync(await fs.readFile(`${root}/${phase}/${device}/contact-frames.json.gz`)));
  const contacts={};const anchors=new Map();
  for(const sample of contact.samples)for(const foot of sample.feet){
    const stats=contacts[foot.morph]||={clearance:[],drift:[]};
    const key=`${foot.id}:${foot.leg}`;
    if(!foot.stance){anchors.delete(key);continue;}
    stats.clearance.push(foot.soleWorldY ?? foot.soleClearance + contact.referenceSurfaceY);
    const anchor=anchors.get(key);
    if(anchor&&anchor.cycle===foot.cycle&&sample.time-anchor.last<220){stats.drift.push(Math.hypot(foot.x-anchor.x,foot.z-anchor.z));anchor.last=sample.time;}
    else anchors.set(key,{...foot,last:sample.time});
  }
  const first=raw.samples[0],last=raw.samples.at(-1);
  summary.runs[`${phase}/${device}`]={environment:raw.environment,errors:raw.errors,ui:raw.ui,inputCheck:raw.inputCheck,
    cameras:raw.segments.map(s=>({camera:s.camera,requestedFocus:s.focus,frames:s.frames.length,fps:1000/mean(s.frames),p95FrameMs:percentile(s.frames,.95),videoStartSeconds:s.start/1000,videoEndSeconds:s.end/1000})),
    calls:[...new Set(raw.samples.map(s=>s.calls))],triangles:[...new Set(raw.samples.map(s=>s.triangles))],
    colorVersionDelta:Object.fromEntries(Object.keys(first.colorVersions).map(k=>[k,last.colorVersions[k]-first.colorVersions[k]])),
    contactMethod:contact.method,
    contacts:Object.fromEntries(Object.entries(contacts).map(([m,s])=>[m,{stanceSamples:s.clearance.length,driftSamples:s.drift.length,minClearance:Math.min(...s.clearance),medianClearance:percentile(s.clearance,.5),p95Clearance:percentile(s.clearance,.95),p95SampledDrift:percentile(s.drift,.95),maxSampledDrift:s.drift.length?Math.max(...s.drift):null}]))};
}
console.log(JSON.stringify(summary,null,2));

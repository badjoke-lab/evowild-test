import fs from 'node:fs';import {gunzipSync} from 'node:zlib';import {summarizeBodyReturn} from './measure_s_body_return.mjs';
const root='docs/2p5d/evidence',out=`${root}/20261028-s-return-d2c2`,reports=[];
for(const [label,path] of [['before',`${root}/20261028-s-return-d2c1/before-return-trace.json.gz`],['after',`${out}/after-return-trace.json.gz`]]){
 const data=JSON.parse(gunzipSync(fs.readFileSync(path))),full=data.traces[1];
 const rows=full.rows.filter(r=>r.phase>=.44-1e-10&&r.phase<=.62+1e-10);
 const summary=summarizeBodyReturn({...data,traces:[{...full,range:[.44,.62],rows}]});
 const n=v=>Math.hypot(...v),sub=(a,b)=>a.map((v,i)=>v-b[i]),dt=full.dt;
 const points=rows.map(r=>r.bodyPoints.map(p=>p.map((v,i)=>v-(i===2?r.distance:0))));
 let meshSpeed=0,meshAccel=0;
 const velocities=[];
 for(let i=1;i<points.length;i++){const v=points[i].map((p,j)=>sub(p,points[i-1][j]).map(x=>x/dt));meshSpeed=Math.max(meshSpeed,...v.map(n));velocities.push(v);if(i>1)meshAccel=Math.max(meshAccel,...v.map((p,j)=>n(sub(p,velocities.at(-2)[j]))/dt));}
 const supports=rows.map(r=>({phase:r.phase,relative:r.contact.limbs.flatMap(l=>l.anchor?[{name:l.name,pelvisToAnchor:sub(r.body.find(b=>b.name==='pelvis').position,l.anchor)}]:[])}));
 reports.push({label,window:[.44,.62],samples:rows.length,dt,meshSpeed,meshAccel,...summary,supports});
}
fs.writeFileSync(`${out}/return-comparison.json`,JSON.stringify(reports,null,2)+'\n');
for(const r of reports)console.log(r.label,JSON.stringify({meshSpeed:r.meshSpeed,meshAccel:r.meshAccel,parts:r.ranges[0].parts}));

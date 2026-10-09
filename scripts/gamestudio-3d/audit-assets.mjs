import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const files=execFileSync('git',['ls-files','public/models','public/concept','docs/references','docs/creature-reference-index-v0.1.md','docs/motion-first-creature-standard-v0.1.md','docs/s-hunyuan-canonical.md'],{encoding:'utf8'}).trim().split('\n');
const assets=[];
for(const file of files){
  const data=await fs.readFile(file);const item={file,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')};
  if(file.endsWith('.glb')){
    if(data.toString('ascii',0,4)!=='glTF'||data.readUInt32LE(4)!==2||data.readUInt32LE(8)!==data.length)throw Error(`Invalid GLB: ${file}`);
    const gltf=JSON.parse(data.subarray(20,20+data.readUInt32LE(12)).toString());
    item.gltf={generator:gltf.asset.generator,scenes:gltf.scenes?.length,nodes:gltf.nodes?.length,
      triangles:gltf.meshes.reduce((sum,m)=>sum+m.primitives.reduce((n,p)=>n+((gltf.accessors[p.indices??p.attributes.POSITION].count)/3),0),0),
      skins:(gltf.skins||[]).map(s=>({name:s.name,joints:s.joints.length,bones:s.joints.map(i=>gltf.nodes[i].name)})),
      animations:(gltf.animations||[]).map(a=>({name:a.name,channels:a.channels.length,paths:[...new Set(a.channels.map(c=>c.target.path))],timeBounds:a.samplers.map(s=>({min:gltf.accessors[s.input].min,max:gltf.accessors[s.input].max}))})),
      externalURIs:[...(gltf.buffers||[]),...(gltf.images||[])].flatMap(b=>b.uri&&!b.uri.startsWith('data:')?[b.uri]:[]),
      meshBounds:gltf.meshes.map(m=>({name:m.name,primitives:m.primitives.map(p=>({min:gltf.accessors[p.attributes.POSITION].min,max:gltf.accessors[p.attributes.POSITION].max}))}))};
    item.role=file.includes('v31')?'REJECTED: inventory only, never loaded':file.includes('headfix')?'Non-active candidate: inventory only':file.includes('v5')?'Active S candidate, not final art':'Source/static asset';
  }
  assets.push(item);
}
console.log(JSON.stringify({runtime:'Target uses existing transform-only S/P/E/A proxy rigs and shared instances, not these GLBs. Audit does not promote any asset.',assets},null,2));

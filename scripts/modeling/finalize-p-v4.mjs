// Normalize the identity mesh parent after Blender export. Bone and vertex data
// are untouched. glTF's skin transform contract requires the mesh at scene root.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const asset='public/models/evowild-p/p-canonical-v4.glb';
fs.mkdirSync('work/p-canonical-v4',{recursive:true});
for(const args of [['dedup',asset,'work/p-canonical-v4/p-dedup.glb'],['prune','work/p-canonical-v4/p-dedup.glb',asset]]){
 execFileSync('npx',['--yes','@gltf-transform/cli@4.3.0',...args],{stdio:'inherit',env:{...process.env,npm_config_cache:`${process.cwd()}/work/npm-cache`}});
}
const b=fs.readFileSync(asset),jsonLength=b.readUInt32LE(12),gltf=JSON.parse(b.subarray(20,20+jsonLength));
for(let i=0;i<gltf.nodes.length;i++){
 const node=gltf.nodes[i];if(node.skin===undefined)continue;
 for(const parent of gltf.nodes){
  if(!parent.children?.includes(i))continue;
  if(parent.matrix||parent.translation||parent.rotation||parent.scale)throw Error('Refusing to flatten a non-identity skin parent');
  parent.children=parent.children.filter(n=>n!==i);
  for(const scene of gltf.scenes)if(!scene.nodes.includes(i))scene.nodes.push(i);
 }
}
let encoded=Buffer.from(JSON.stringify(gltf));encoded=Buffer.concat([encoded,Buffer.alloc((4-encoded.length%4)%4,32)]);
const rest=b.subarray(20+jsonLength),header=Buffer.alloc(20);b.copy(header,0,0,20);header.writeUInt32LE(20+encoded.length+rest.length,8);header.writeUInt32LE(encoded.length,12);
fs.writeFileSync(asset,Buffer.concat([header,encoded,rest]));
console.log('Finalized',asset,fs.statSync(asset).size,'bytes');

const manifestPath='public/models/evowild-p/manifest-v4.json';
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
Object.assign(manifest,{bytes:fs.statSync(asset).size,sha256:createHash('sha256').update(fs.readFileSync(asset)).digest('hex'),packaging:'glTF Transform 4.3.0 dedup/prune; identity mesh parent normalized to scene root',materials:gltf.materials.length,externalURIs:[...gltf.buffers,...(gltf.images||[])].filter(x=>x.uri).map(x=>x.uri),runtimeScope:'isolated shape and minimal motion review; production HOLD'});
fs.writeFileSync(manifestPath,JSON.stringify(manifest,null,2)+'\n');

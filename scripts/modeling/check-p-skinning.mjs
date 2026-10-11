// Inspect the actual delivered GLB with Three.js, independently of Blender.
import fs from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const file=process.argv[2]||'public/models/evowild-p/p-canonical-v5.glb';
const bytes=fs.readFileSync(file);
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const clip=gltf.animations[0],mixer=new THREE.AnimationMixer(gltf.scene);
const action=mixer.clipAction(clip);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;
const meshes=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});
const footVertices=[];
for(const mesh of meshes){
 const si=mesh.geometry.attributes.skinIndex,sw=mesh.geometry.attributes.skinWeight;
 for(let i=0;i<si.count;i++)for(let j=0;j<4;j++){
  const bone=mesh.skeleton.bones[si.getComponent(i,j)]?.name;
  if(bone?.endsWith('_foot')&&sw.getComponent(i,j)>.99)footVertices.push({mesh,i,tag:bone.slice(0,2)});
 }
}
const v=new THREE.Vector3();
function pose(t){action.reset().play();mixer.setTime(t);gltf.scene.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();}
function positions(){return meshes.map(m=>{
 const a=new Float32Array(m.geometry.attributes.position.count*3);
 for(let i=0;i<a.length/3;i++){m.getVertexPosition(i,v).applyMatrix4(m.matrixWorld);v.toArray(a,i*3);}
 return a;
});}
pose(0);const first=positions();pose(clip.duration);const last=positions();
let maxLoopDelta=0;for(let m=0;m<first.length;m++)for(let i=0;i<first[m].length;i++)maxLoopDelta=Math.max(maxLoopDelta,Math.abs(first[m][i]-last[m][i]));
const samples=[],tags=['FL','FR','HL','HR'];
for(let f=0;f<=96;f++){
 const phase=(f%24)/24;pose((f%24)/30);
 const feet=Object.fromEntries(tags.map(t=>[t,{minY:Infinity,sumX:0,count:0,stance:(phase+{HL:0,HR:.12,FL:.48,FR:.60}[t])%1<.62}]));
 for(const {mesh,i,tag} of footVertices){mesh.getVertexPosition(i,v).applyMatrix4(mesh.matrixWorld);const foot=feet[tag];foot.minY=Math.min(foot.minY,v.y);foot.sumX+=v.x;foot.count++;}
 for(const foot of Object.values(feet)){foot.meanX=foot.sumX/foot.count;delete foot.sumX;}
 samples.push({frame:f,time:f/30,feet});
}
const ground={};
for(const tag of tags){
 const ys=samples.filter(s=>s.feet[tag].stance).map(s=>s.feet[tag].minY);
 const velocities=[];
 for(let i=1;i<samples.length;i++)if(samples[i-1].feet[tag].stance&&samples[i].feet[tag].stance&&samples[i].frame%24!==0)velocities.push((samples[i].feet[tag].meanX-samples[i-1].feet[tag].meanX)*30);
 ground[tag]={stanceMinY:Math.min(...ys),stanceMaxY:Math.max(...ys),meanStanceVelocityX:velocities.reduce((a,b)=>a+b,0)/velocities.length};
}
const report={asset:file,engine:'Three.js GLTFLoader + actual skinned vertex evaluation',durationSeconds:clip.duration,
 maxLoopEndpointVertexDeltaMetres:maxLoopDelta,cyclesInVideoPerView:3.2/clip.duration,
 footVertexSamples:footVertices.length,ground,
 interpretation:'In-place shape review only. Fore/hind stance X speeds differ: a shared moving ground cannot lock every sole. Ground contact and production gait remain unapproved.',samples};
if(Math.abs(clip.duration-.8)>1e-5)throw Error(`Unexpected cycle duration ${clip.duration}`);
if(maxLoopDelta>1e-4)throw Error(`Loop endpoint gap ${maxLoopDelta}`);
fs.writeFileSync('docs/evidence/p-canonical-3d-v5-20261011/skin-motion-validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,samples:undefined},null,2));

import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {preparePose} from '../public/exp-sprite-stacking/runtime/pose.js';
const out='work/sprite-stacking/poses';await fs.mkdir(out,{recursive:true});
const file='public/exp-sprite-stacking/assets/source.glb',buffer=await fs.readFile(file);
const gltf=await new GLTFLoader().parseAsync(buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength),'');
const p=preparePose(gltf),g=p.mesh.geometry,n=g.attributes.position.count;
const positions=new Float32Array(n*3),normals=new Float32Array(n*3),v=new THREE.Vector3(),mat=new THREE.Matrix4(),bone=new THREE.Matrix4(),normal=new THREE.Matrix3();
const indices=Uint32Array.from(g.index?g.index.array:Array.from({length:n},(_,i)=>i));await fs.writeFile(path.join(out,'indices.bin'),Buffer.from(indices.buffer));
const samples=[],poseFrames=[];let min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
for(let f=0;f<48;f++){
 if(f)p.advance(p.period/48);p.localize();
 for(let i=0;i<n;i++){
  p.mesh.getVertexPosition(i,v).applyMatrix4(p.mesh.matrixWorld);v.toArray(positions,i*3);
  for(let k=0;k<3;k++){min[k]=Math.min(min[k],v.getComponent(k));max[k]=Math.max(max[k],v.getComponent(k));}
  mat.elements.fill(0);
  for(let j=0;j<4;j++){const w=g.attributes.skinWeight.getComponent(i,j),id=g.attributes.skinIndex.getComponent(i,j);bone.fromArray(p.mesh.skeleton.boneMatrices,id*16);for(let k=0;k<16;k++)mat.elements[k]+=bone.elements[k]*w;}
  mat.premultiply(p.mesh.bindMatrixInverse).multiply(p.mesh.bindMatrix).premultiply(p.mesh.matrixWorld);
  normal.getNormalMatrix(mat);v.fromBufferAttribute(g.attributes.normal,i).applyMatrix3(normal).normalize().toArray(normals,i*3);
 }
 await fs.writeFile(path.join(out,`${String(f).padStart(2,'0')}.bin`),Buffer.concat([Buffer.from(positions.buffer),Buffer.from(normals.buffer)]));
 poseFrames.push(Object.fromEntries([...p.mesh.skeleton.bones,p.mesh.parent].map(b=>[b.name,{p:b.position.toArray(),q:b.quaternion.toArray(),s:b.scale.toArray()}])));
 samples.push({frame:f,phase:f/48,soles:p.soles(),bones:Object.fromEntries(['fore_L_scapula','fore_R_scapula','chest','pelvis','head','tail'].map(name=>{const b=p.mesh.skeleton.bones.find(b=>b.name===name);return [name,{position:b.getWorldPosition(new THREE.Vector3()).toArray(),quaternion:b.getWorldQuaternion(new THREE.Quaternion()).toArray()}];}))});
 if(f%12===0)console.log('Pose',f);
 // Restore travelled distance for authoritative next integrated step.
 p.root.position.z=p.ik.state.distance;p.root.updateMatrixWorld(true);
}
const manifest={source:file,sourceSha256:crypto.createHash('sha256').update(buffer).digest('hex'),referenceSha256:crypto.createHash('sha256').update(await fs.readFile('public/exp-sprite-stacking/assets/reference.png')).digest('hex'),vertices:n,triangles:indices.length/3,min,max,frames:48,period:p.period,stride:p.stride,hasTexture:false,hasVertexColors:false,alphaMode:'OPAQUE source; transparent outside cross-section',sourceCommit:'ec9695146e78a24b39bfa9fca7c5d87e89564a6e',samples};
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2));console.log('Bounds',min,max);

await fs.writeFile('public/exp-sprite-stacking/assets/pose-tracks.json',JSON.stringify(poseFrames));

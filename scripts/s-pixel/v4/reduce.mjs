// Each LOD starts with the same shell. Position optimization can balance
// errors on both sides of a curved contour while locked extremities stay put.
import fs from 'node:fs';
import {MeshoptSimplifier} from '../v3/node_modules/meshoptimizer/meshopt_simplifier.module.js';
const [vertices, indices, ...targets]=process.argv.slice(2).map(Number);
const input=new Uint8Array(fs.readFileSync(0)).buffer;
const positions=new Float32Array(input,0,vertices*3);
const faces=new Uint32Array(input,positions.byteLength,indices);
const locks=new Uint8Array(input,positions.byteLength+faces.byteLength);
await MeshoptSimplifier.ready;
for(const target of targets){
 const p=positions.slice(), f=faces.slice();
 const [count]=MeshoptSimplifier.simplifyWithUpdate(f,p,3,new Float32Array(0),0,[],locks,target*3,1);
 const header=Buffer.alloc(4);
 header.writeUInt32LE(count);
 fs.writeSync(1,header);
 fs.writeSync(1,Buffer.from(p.buffer));
 fs.writeSync(1,Buffer.from(f.buffer,0,count*4));
}

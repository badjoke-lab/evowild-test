// Reconstruct the actual current race proxy without changing its proportions.
// Source: origin/main cde1bd7, public/preview-motion-first/main.js.
import fs from 'node:fs';
import vm from 'node:vm';
import * as THREE from 'three';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
const source=fs.readFileSync('public/preview-motion-first/main.js','utf8');
function fn(name){const start=source.indexOf(`function ${name}(`);if(start<0)throw Error(name);let i=source.indexOf('{',start),n=1,end=i+1;for(;n;end++){if(source[end]==='{')n++;if(source[end]==='}')n--;}return source.slice(start,end);}
// makeMesh has default array parameters but no object destructuring; brace extraction is safe here.
const profile=source.slice(source.indexOf('const RACE_PROXY_PROFILE ='),source.indexOf('const proxyBodyGeometry ='));
const geometries=source.slice(source.indexOf('const proxyBodyGeometry ='),source.indexOf('let simplifiedRaceProxyPool ='));
const context=vm.createContext({THREE});
vm.runInContext(`const TAU=Math.PI*2; const MORPHS={P:{}};const P_GAIT={minStrideWorld:1,baseY:2.04};\n${profile}\n${geometries}\n${['mat','makeMesh','makeTaperedPlate','makePowerLimb','createPowerCreature','createSimplifiedRaceProxy'].map(fn).join('\n')}\n globalThis.proxy=createSimplifiedRaceProxy('P',0x4fa4ff,createPowerCreature(0x4fa4ff,1));\nglobalThis.geometries={chest:proxyBodyGeometry,waistPart:proxyBodyGeometry,collar:proxyBodyGeometry,pelvis:proxyBodyGeometry,neck:proxyNeckGeometry,headPart:proxyHeadGeometry,muzzle:proxyMuzzleGeometry,crest:proxyCrestGeometry,cue:proxyCueGeometry,tailBlade:proxyTailBladeGeometry,tailParts:proxyTailGeometry,upper:proxyLegGeometry,lower:proxyLowerLegGeometry,cannon:proxyCannonGeometry,footPart:proxyFootGeometry,toes:proxyToeGeometry};`,context);
const proxy=context.proxy,meta=proxy.userData.raceProxy;
const group=new THREE.Group();group.name='Previous_P_race_proxy';proxy.updateMatrixWorld(true);
const mats={};for(const [k,v]of Object.entries(meta.colors)) mats[k]=new THREE.MeshStandardMaterial({color:v,roughness:.8,flatShading:true});
function part(node,key,color){const m=new THREE.Mesh(context.geometries[key],mats[color]);m.name=`previous_${key}`;m.applyMatrix4(node.matrixWorld);group.add(m);}
for(const key of ['chest','waistPart','collar','pelvis','neck','headPart','muzzle','crest','cue','tailBlade'])part(meta[key],key,key==='cue'?'cue':['pelvis','muzzle','crest','tailBlade'].includes(key)?'secondary':'primary');
for(const node of meta.tailParts)part(node,'tailParts','secondary');
for(const leg of meta.legs){for(const key of ['upper','lower','cannon','footPart'])part(leg[key],key,['lower','footPart'].includes(key)?'dark':'primary');for(const node of leg.toes)part(node,'toes','dark');}
// Original +Z-forward -> candidate -X-forward. Ground each by its own sole; no shape scaling.
group.rotation.y=-Math.PI/2;group.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(group);group.position.y-=box.min.y;
group.position.x-=(box.max.x+box.min.x)/2;
// Node export polyfill only; buffer serialization remains the official Three GLTFExporter.
globalThis.FileReader=class{readAsArrayBuffer(blob){blob.arrayBuffer().then(b=>{this.result=b;this.onloadend?.();});}};
const buffer=await new GLTFExporter().parseAsync(group,{binary:true});
fs.writeFileSync('docs/evidence/p-canonical-3d-20261011/previous-proxy.glb',Buffer.from(buffer));
console.log('Exported actual race proxy rest geometry',group.children.length,'meshes');

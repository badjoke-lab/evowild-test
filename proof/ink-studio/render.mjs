import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import sharp from 'sharp';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const [up,source,output]=process.argv.slice(2).map(x=>path.resolve(x));
fs.mkdirSync(output,{recursive:true});
const req=createRequire(import.meta.url), studio=req(path.join(up,'index.js'));
const {makeBuilder,makeSculpt,KIT:K}=studio.load();
const R=req(path.join(up,'cli/render.js')), PNG=req(path.join(up,'cli/png.js'));
const bytes=fs.readFileSync(source), digest=createHash('sha256').update(bytes).digest('hex');
const n=bytes.readUInt32LE(12), doc=JSON.parse(bytes.subarray(20,20+n));
const binary=bytes.subarray(28+n);
const original=structuredClone(doc), textures=new Map();
for(const [i,t] of (original.textures||[]).entries()){
  const image=original.images?.[t.source];if(!image)continue;
  let encoded;
  if(image.bufferView!=null){const b=original.bufferViews[image.bufferView];encoded=binary.subarray(b.byteOffset||0,(b.byteOffset||0)+b.byteLength)}
  else if(image.uri?.startsWith('data:'))encoded=Buffer.from(image.uri.split(',')[1],'base64');
  else continue;
  const {data,info}=await sharp(encoded).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  textures.set(i,{pixels:data,width:info.width,height:info.height,sampler:original.samplers?.[t.sampler]||{}});
}
function wrap(v,k){if(k===33071)return Math.max(0,Math.min(1-1e-8,v));if(k===33648){const f=((v%2)+2)%2;return Math.min(1-1e-8,f>1?2-f:f)}return v-Math.floor(v)}
const linear=x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4;
const srgb=x=>THREE.ColorManagement.workingToColorSpace(new THREE.Color(x,x,x),THREE.SRGBColorSpace).r;
function materialInfo(m){
  const a=gltf.parser.associations.get(m), mi=a?.meshes, pi=a?.primitives;
  let id=mi!=null?original.meshes[mi]?.primitives[pi??0]?.material:undefined;
  if(id==null)id=gltf.parser.associations.get(m.material)?.materials;
  if(id==null&&original.materials?.length===1)id=0;
  if(id==null)id=original.materials?.findIndex(x=>x.name&&x.name===m.material.name);
  const q=original.materials?.[id], p=q?.pbrMetallicRoughness||{}, t=p.baseColorTexture, tx=t&&textures.get(t.index);
  return {id,base:p.baseColorFactor||[1,1,1,1],t,tx};
}
function sample(m,i,info){
  const {base,t,tx}=info, vc=m.geometry.attributes.color;
  let col=[base[0]*(vc?vc.getX(i):1),base[1]*(vc?vc.getY(i):1),base[2]*(vc?vc.getZ(i):1)];
  if(tx){
    const uvIndex=t.extensions?.KHR_texture_transform?.texCoord??t.texCoord??0;
    const uv=m.geometry.attributes[uvIndex===0?'uv':'uv'+uvIndex];
    if(!uv)throw Error('Missing UV for source base color texture');
    let x=uv.getX(i), y=uv.getY(i); const tr=t.extensions?.KHR_texture_transform;
    if(tr){x*=tr.scale?.[0]??1;y*=tr.scale?.[1]??1;const a=tr.rotation||0;[x,y]=[Math.cos(a)*x-Math.sin(a)*y+(tr.offset?.[0]||0),Math.sin(a)*x+Math.cos(a)*y+(tr.offset?.[1]||0)]}
    x=Math.floor(wrap(x,tx.sampler.wrapS)*tx.width);y=Math.floor(wrap(y,tx.sampler.wrapT)*tx.height);
    const at=(y*tx.width+x)*4;
    col=col.map((c,k)=>c*linear(tx.pixels[at+k]/255));
  }
  return col.map(x=>x<=.0031308?12.92*x:1.055*Math.pow(x,1/2.4)-.055).map(x=>Math.max(0,Math.min(1,x)));
}
// Match Ink's documented material support: original geometry, skins, animations,
// base factors and vertex colours; remove texture references only in the in-memory copy.
for(const m of doc.materials||[]){
  for(const k of Object.keys(m)) if(/Texture$/.test(k)) delete m[k];
  for(const k of Object.keys(m.pbrMetallicRoughness||{})) if(/Texture$/.test(k)) delete m.pbrMetallicRoughness[k];
  delete m.extensions;
}
delete doc.images;delete doc.textures;delete doc.samplers;
doc.extensionsUsed=(doc.extensionsUsed||[]).filter(x=>!x.startsWith('KHR_texture'));
doc.extensionsRequired=(doc.extensionsRequired||[]).filter(x=>!x.startsWith('KHR_texture'));
let json=Buffer.from(JSON.stringify(doc));
json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
const hdr=Buffer.alloc(20),binhdr=Buffer.alloc(8);
hdr.writeUInt32LE(0x46546c67,0);hdr.writeUInt32LE(2,4);hdr.writeUInt32LE(28+json.length+binary.length,8);
hdr.writeUInt32LE(json.length,12);hdr.writeUInt32LE(0x4e4f534a,16);
binhdr.writeUInt32LE(binary.length,0);binhdr.writeUInt32LE(0x004e4942,4);
const glb=Buffer.concat([hdr,json,binhdr,binary]);
globalThis.ProgressEvent??=class ProgressEvent{constructor(type,props){this.type=type;Object.assign(this,props)}};
const gltf=await new GLTFLoader().parseAsync(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength),'');
const clip=gltf.animations.find(c=>c.name==='EvoWild_S_D3C_V3');
if(!clip)throw Error('Required full native clip missing');
const root=gltf.scene, meshes=[];
root.traverse(o=>{if(o.isMesh)meshes.push(o)});
if(!meshes.some(x=>x.isSkinnedMesh))throw Error('Missing skinned source');
const colorCache=new Map();
const materialAudit=meshes.map(m=>{const info=materialInfo(m),v=m.geometry.attributes.position.count,colors=new Float32Array(v*3);
for(let i=0;i<v;i++)colors.set(sample(m,i,info),3*i);colorCache.set(m,colors);
return {name:m.name,material:info.id,base:info.base,texture:info.tx?{width:info.tx.width,height:info.tx.height}:null,vertexColor:!!m.geometry.attributes.color,vertices:v};
});
console.log('SOURCE_COLORS',JSON.stringify(materialAudit));
const mixer=new THREE.AnimationMixer(root);
const action=mixer.clipAction(clip);action.play();
const v=new THREE.Vector3(), c=new THREE.Color();
function geometry(t){
  mixer.setTime(t);root.updateMatrixWorld(true);
  for(const m of meshes)if(m.isSkinnedMesh)m.skeleton.update();
  const pos=[],tri=[],vcol=[],tmat=[],mats=[];
  for(const m of meshes){
    const g=m.geometry, a=g.attributes.position, vc=g.attributes.color, off=pos.length/3;
    const material=Array.isArray(m.material)?m.material[0]:m.material;
    c.copy(material.color||new THREE.Color(0.7,0.7,0.7));
    const mid=mats.length;mats.push({name:material.name||m.name,rgb:[c.r,c.g,c.b]});
    for(let i=0;i<a.count;i++){
      m.getVertexPosition(i,v);v.applyMatrix4(m.matrixWorld);
      pos.push(v.x,v.y,v.z);
      const colors=colorCache.get(m);vcol.push(colors[i*3],colors[i*3+1],colors[i*3+2]);
    }
    const ix=g.index, len=ix?ix.count:a.count;
    if(len%3)throw Error('Non-triangle primitive');
    for(let i=0;i<len;i+=3){tri.push(off+(ix?ix.getX(i):i),off+(ix?ix.getX(i+1):i+1),off+(ix?ix.getX(i+2):i+2));tmat.push(mid)}
  }
  if(!pos.every(Number.isFinite))throw Error('Invalid skinned vertex');
  return K.mesh.make(pos,tri,vcol,tmat,mats);
}
const raw=geometry(0), bounds=K.mesh.box(raw), span=Math.max(...bounds.hi.map((v,i)=>v-bounds.lo[i]));
if(!(span>0))throw Error('Invalid mesh bounds');
const scale=6/span, center=[(bounds.lo[0]+bounds.hi[0])/2,bounds.lo[1],(bounds.lo[2]+bounds.hi[2])/2];
function fixedMesh(mesh){
  for(let i=0;i<mesh.pos.length;i++)mesh.pos[i]=(mesh.pos[i]-center[i%3])*scale;
  return mesh;
}
const fitted=fixedMesh(raw), look=K.mesh.look(fitted,{hues:7,shades:5});
const target=[0,(bounds.hi[1]-bounds.lo[1])*scale/2,0],dist=13;
function bake(mesh,res=.085){
  const B=makeBuilder(7,look.pal),S=K.sculpt(makeSculpt(B));
  S.mesh(mesh,K.mesh.look(mesh,{pal:look.pal,hues:7,shades:5}),{cells:64,res});S.bake();
  return B.finish({cam:{target,dist,pitch:.13,yaw:Math.PI/2},detail:16,dither:.2,radius:8});
}
function alphaFrame(world,options,filename){
  const img=R.render(world,options),mask=R.render(world,{...options,colored:false,captureCoverage:true});
  if(img.w!==mask.w||img.h!==mask.h)throw Error('Coverage dimensions');
  const rgba=new Uint8Array(img.w*img.h*4);
  let occupied=0;
  for(let i=0;i<mask.coverage.length;i++){
    rgba[i*4]=img.rgb[i*3];rgba[i*4+1]=img.rgb[i*3+1];rgba[i*4+2]=img.rgb[i*3+2];
    const x=i%img.w,y=Math.floor(i/img.w);
    const a=mask.coverage[(img.h-1-y)*img.w+x];rgba[i*4+3]=a>.25?255:0;if(a>.25)occupied++;
  }
  if(occupied<50)throw Error('Empty rendered frame');
  const buf=PNG.encode(img.w,img.h,rgba,4);fs.writeFileSync(path.join(output,filename),buf);
  return {file:filename,splats:world.count,occupied,sha:createHash('sha256').update(buf).digest('hex')};
}
const baseOpts={w:384,h:256,px:2,ortho:true,colored:true,pitch:.13};
const views=[];
const rest=bake(fitted);
for(const [name,yaw] of [['side',Math.PI/2],['front',0],['front34',Math.PI/4],['rear34',3*Math.PI/4],['back',Math.PI]]){
  views.push(alphaFrame(rest,{...baseOpts,yaw},'view-'+name+'.png'));console.log('VIEW',name,views.at(-1).splats);
}
const frames=[],splatFrames=[],count=24;
function compact(w){
  const out=new Float32Array(w.count*11);
  for(let i=0;i<w.count;i++)out.set(w.data.subarray(i*16,i*16+11),i*11);
  if(!out.every(Number.isFinite))throw Error('Invalid splat data');
  return out;
}
for(let f=0;f<count;f++){
  const t=clip.duration*f/count, world=bake(fixedMesh(geometry(t)));
  splatFrames.push(compact(bake(fixedMesh(geometry(t)),.135)));
  frames.push({...alphaFrame(world,{...baseOpts,yaw:Math.PI/2},'run-'+String(f).padStart(2,'0')+'.png'),t});
  console.log('FRAME',f,world.count);
}
if(new Set(frames.map(f=>f.sha)).size<12)throw Error('Motion sequence lacks distinct images');
// Course built using Ink's actual SDF sculpt and Gaussian splat renderer.
const palette=[0x102127,0x223f37,0x385746,0x567751,0x8b9b65,0x5a4635,0x886746,0xb89465,0xdec28a,0x485b5c,0x718181,0xb6babe,0x30463d,0x6c9055,0xd6cf90];
const B=makeBuilder(82,palette), S=K.sculpt(makeSculpt(B));
S.box([0,-.65,0],[8,.65,13],{r:[1,2,3,4]},{res:.48});
S.box([0,.01,0],[3.65,.045,12.4],{r:[5,6,7,8]},{res:.34});
for(let i=0;i<17;i++){
  const z=-11.8+1.47*i,x=i%2===0?5.4:-5.4;
  S.ball([x,.5,z],[.8,.5,.72],{r:[1,2,3,4]},{res:.36});
  const h=1.3+.4*Math.sin(i*2);
  S.tube([[x,.2,z],[x,h,z]],.13,.09,{r:[5,6,7]},{res:.3});
  S.ball([x,h+.55,z],[.7,.8,.65],{r:[1,3,13,4]},{res:.3});
}
for(let i=0;i<14;i++){
  const z=-12+1.8*i;
  for(const x of [-3.9,3.9])S.ball([x,.12,z],[.28,.22,.4],{r:[9,10,11]},{res:.24});
}
S.bake();
const course=B.finish({cam:{target:[0,0,0],dist:36,pitch:.58,yaw:Math.PI/2},detail:14,dither:.25,radius:20});
const bg=R.render(course,{w:960,h:480,px:3,ortho:true,colored:true});
fs.writeFileSync(path.join(output,'course.png'),PNG.encode(bg.w,bg.h,bg.rgb));
const report={materialAudit,source,sourceSha256:digest,clip:clip.name,duration:clip.duration,sourceVertices:raw.pos.length/3,sourceTriangles:raw.tri.length/3,views,frames,courseSplats:course.count,limitations:['Baked splat frames displayed as sprites; not live 3D Gaussian rendering','Base-color textures sampled at existing vertices (when present); Ink palette quantization; no other PBR channels','Native full clip, without existing runtime contact IK','Independent 4-runner toy race, not existing race-system integration']};
fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));
const image=file=>'data:image/png;base64,'+fs.readFileSync(path.join(output,file)).toString('base64');
const assets={background:image('course.png'),frames:frames.map(f=>image(f.file)),duration:clip.duration};
const html=fs.readFileSync(new URL('./race.html',import.meta.url),'utf8').replace('/*__ASSETS__*/null',JSON.stringify(assets));
fs.writeFileSync(path.join(output,'race.html'),html);
console.log('RENDER_DONE',JSON.stringify({frames:frames.length,courseSplats:course.count,duration:clip.duration}));

const sceneData=[compact(course),...splatFrames];
const pack=Buffer.concat(sceneData.map(a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength)));
const payload={counts:sceneData.map(a=>a.length/11),duration:clip.duration,bytes:pack.length,gzip:gzipSync(pack).toString('base64'),sourceSha256:digest,revision:'live-3d-2'};
const live=fs.readFileSync(new URL('./live.html',import.meta.url),'utf8').replace('/*__LIVE__*/null',JSON.stringify(payload));
fs.writeFileSync(path.join(output,'live-race.html'),live);
console.log('LIVE_PACK',JSON.stringify({counts:payload.counts,bytes:pack.length,compressed:payload.gzip.length}));

import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {identifyFootSurfaces,sampleFootSurfaces} from './s_foot_contact_geometry.js';
import {createContactIK} from './s_contact_ik.js';
import {createBodyCoupling} from './s_body_coupling.js';
import {selectSolePatches,sampleSoles} from './s_sole_metrics.js';

const rig=new URLSearchParams(location.search).get('rig');
const assets={'bind-v1':'review/focus-bind-repair-v1.glb','hind-v2':'review/focus-hind-fit-v2.glb','contact-v3':'review/focus-contact-v3.glb'};
const asset=assets[rig] || 'focus-rigged-v5.glb';
if(assets[rig])document.querySelector('header small').textContent=`S ${rig} · 原本の頂点・面を保持 / REVISE・本番未採用`;
const canvas=document.querySelector('#view');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
renderer.shadowMap.enabled=true;
renderer.setClearColor('#647c8d');
const scene=new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xe3f4ff,0x585746,2));
const sun=new THREE.DirectionalLight(0xfff5dc,3);sun.position.set(5,9,-4);sun.castShadow=true;
sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-8,right:8,top:8,bottom:-8,near:.1,far:30});scene.add(sun,sun.target);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(160,160),new THREE.MeshStandardMaterial({color:0x7f7864,roughness:1}));ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
const grid=new THREE.GridHelper(160,160,0x344b5a,0xa3aa9c);grid.position.y=.002;scene.add(grid);
const camera=new THREE.PerspectiveCamera(42,1,.05,240);
const root=new THREE.Group();scene.add(root);
const views={SIDE:[10,2.8,0],CHASE:[1.8,3.0,-8],LOW:[2.2,.9,-7.5],REAR_3_4:[5,2.6,-7]};
let model,mixer,clip,mesh,bodyCoupling,rate=1,time=0,paused=false,last=0;
const speedMeters=4; // Isolated diagnostic translation, not a race balance value.
const feet=[];let solePatches,contactIK,contactState,footSurfaces;
const v=new THREE.Vector3();
function updateCamera(){const offset=views[document.querySelector('#camera').value];camera.position.set(offset[0],offset[1],root.position.z+offset[2]);camera.lookAt(0,1.3,root.position.z);sun.position.z=root.position.z-4;sun.target.position.z=root.position.z;}
function sample(){
  root.updateMatrixWorld(true);mesh.skeleton.update();
  const observations=feet.map(foot=>{
    const p=new THREE.Vector3();
    for(const i of foot.vertices){mesh.getVertexPosition(i,v);p.add(v.applyMatrix4(mesh.matrixWorld));}
    p.multiplyScalar(1/foot.vertices.length);foot.marker.position.copy(p);
    return {name:foot.name,weightBone:foot.weightBone,maxFootInfluence:foot.maxFootInfluence,x:p.x,y:p.y,z:p.z};
  });
  return {time,phase:(time%clip.duration)/clip.duration,rate,distance:root.position.z,
    asset,contact:contactState,camera:document.querySelector('#camera').value,clip:clip.name,duration:clip.duration,
    bones:mesh.skeleton.bones.length,vertices:mesh.geometry.attributes.position.count,feet:observations};
}
function bodySample(){
 root.updateMatrixWorld(true);mesh.skeleton.update();
 return mesh.skeleton.bones.filter(b=>!b.name.startsWith('fore_')&&!b.name.startsWith('hind_')).map(b=>({name:b.name,position:b.getWorldPosition(new THREE.Vector3()).toArray(),quaternion:b.getWorldQuaternion(new THREE.Quaternion()).toArray(),localQuaternion:b.quaternion.toArray()}));
}
function render(){updateCamera();const state=sample();renderer.render(scene,camera);document.querySelector('#status').textContent=`${state.camera} · ${contactIK?'Contact IK v3 + native body':state.clip} · 位相 ${state.phase.toFixed(2)} · ${rate}×`;canvas.dataset.ready='1';canvas.dataset.time=String(time);return state;}
function pose(){mixer.setTime(time);bodyCoupling?.apply(time);root.updateMatrixWorld(true);if(contactIK)contactState=contactIK.apply();}
function step(dt){
  if(contactIK){const state=contactIK.advance(dt,rate);time=state.cycles*clip.duration;root.position.z=state.distance;}
  else {time+=dt*rate;root.position.z+=dt*rate*speedMeters;}
  pose();
}
function advance(dt){step(dt);return render();}
function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(model){if(!paused)advance(dt);else render();}requestAnimationFrame(frame);}
function resize(){renderer.setSize(innerWidth,innerHeight,false);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}
addEventListener('resize',resize);resize();
document.querySelector('#speed').onchange=e=>{rate=Number(e.target.value);};
document.querySelector('#pause').onclick=()=>{paused=!paused;document.querySelector('#pause').textContent=paused?'再開':'一時停止';};
try{
  const gltf=await new GLTFLoader().loadAsync(import.meta.env.BASE_URL+'models/evowild-s/'+asset);
  model=gltf.scene;root.add(model);model.rotation.y=0; // Observed mesh head is +Z; keep translation and rear cameras on that axis.
  model.updateMatrixWorld(true);
  let bounds=new THREE.Box3().setFromObject(model);
  model.scale.setScalar(2.85/(bounds.max.y-bounds.min.y));model.updateMatrixWorld(true);
  bounds=new THREE.Box3().setFromObject(model);const center=bounds.getCenter(new THREE.Vector3());
  model.position.set(-center.x,-bounds.min.y,-center.z);
  model.traverse(n=>{if(n.isMesh){n.castShadow=true;n.receiveShadow=true;n.frustumCulled=false;}if(n.isSkinnedMesh)mesh=n;});
  if(!mesh||!gltf.animations.length)throw Error('Canonical skinned mesh/animation missing; no static fallback.');
  model.updateMatrixWorld(true);mesh.skeleton.update();
  // Observe original weight groups, NOT verified anatomical soles. Bad weights are a diagnostic result.
  const {position,skinIndex,skinWeight}=mesh.geometry.attributes;
  for(const name of ['fore_L_foot','fore_R_foot','hind_L_foot','hind_R_foot']){
    let boneIndex=mesh.skeleton.bones.findIndex(b=>b.name===name);
    let influence=0;
    for(let i=0;i<position.count;i++)for(let j=0;j<4;j++)if(skinIndex.getComponent(i,j)===boneIndex)influence=Math.max(influence,skinWeight.getComponent(i,j));
    const weightBone=['hind-v2','contact-v3'].includes(rig)&&name.startsWith('hind_')?name.replace('_foot','_toe'):(influence>0?name:name.replace('_foot','_lower'));
    boneIndex=mesh.skeleton.bones.findIndex(b=>b.name===weightBone);
    const points=[];
    for(let i=0;i<position.count;i++){
      let weight=0;for(let j=0;j<4;j++)if(skinIndex.getComponent(i,j)===boneIndex)weight+=skinWeight.getComponent(i,j);
      if(weight>.1){mesh.getVertexPosition(i,v);v.applyMatrix4(mesh.matrixWorld);points.push({i,y:v.y});}
    }
    points.sort((a,b)=>a.y-b.y);const vertices=points.slice(0,Math.max(1,Math.ceil(points.length*.15))).map(p=>p.i);
    if(!vertices.length)throw Error('Missing weighted foot: '+name);
    const marker=new THREE.Mesh(new THREE.SphereGeometry(.035,8,6),new THREE.MeshBasicMaterial({color:name.startsWith('fore')?0x66ffff:0xffbd68}));scene.add(marker);feet.push({name,vertices,marker,weightBone,maxFootInfluence:influence});
  }
  solePatches=selectSolePatches(mesh);
  if(rig==='contact-v3')footSurfaces=identifyFootSurfaces(mesh,solePatches);
  const toeMode=new URLSearchParams(location.search).get('toe');
  if(rig==='contact-v3')contactIK=createContactIK(mesh,solePatches,{toeSurfaces:['roll-v1','roll-v2','roll-v3'].includes(toeMode)?footSurfaces:null,continuousToe:['roll-v2','roll-v3'].includes(toeMode),toeRoundingWidth:toeMode==='roll-v3'?.0015:.003});
  clip=gltf.animations.find(a=>a.name==='EvoWild_S_Run_V5');if(!clip)throw Error('Expected native run clip missing');
  const bodyMode=new URLSearchParams(location.search).get('body');
  if(rig==='contact-v3'&&['push-v1','push-v2'].includes(bodyMode))bodyCoupling=createBodyCoupling(mesh,clip,{smoothReturn:bodyMode==='push-v2'});
  mixer=new THREE.AnimationMixer(model);mixer.clipAction(clip).play();mixer.setTime(0);if(contactIK){contactIK.reset(0,0,rate);pose();}
  // Isolated review/capture API. Never used by the race or saved as a race result.
  window.sRunReview={sample,advance,step,solePatches,footSurfaces,rollDescriptors:contactIK?.limbs.map(l=>l.roll?{name:l.name,maxDegrees:l.roll.maxDegrees,flatEnd:l.roll.flatEnd,segments:l.roll.segments}:null),footSample(){root.updateMatrixWorld(true);mesh.skeleton.update();return sampleFootSurfaces(mesh,footSurfaces);},probeFootRotation(index,degrees){paused=true;pose();const surface=footSurfaces[index],bone=mesh.skeleton.bones.find(b=>b.name===surface.terminal);const q=bone.getWorldQuaternion(new THREE.Quaternion());const rotation=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),degrees*Math.PI/180).multiply(q);bone.quaternion.copy(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(rotation));root.updateMatrixWorld(true);mesh.skeleton.update();return sampleFootSurfaces(mesh,footSurfaces)[index];},motionSample(){return {time,rate,distance:root.position.z,contact:contactState,soles:sampleSoles(mesh,solePatches)};},setRate(value){rate=value;document.querySelector('#speed').value=String(value);if(contactIK)contactIK.advance(0,value);},soleSample(){root.updateMatrixWorld(true);mesh.skeleton.update();return sampleSoles(mesh,solePatches);},measureCycle(speed=1,steps=240){
    paused=true;rate=speed;document.querySelector('#speed').value=String(speed);const frames=[];
    if(contactIK)contactIK.reset(0,0,speed);
    for(let i=0;i<=steps;i++){
      if(contactIK){if(i)step(contactIK.kinematics(speed).period/steps);else{time=0;root.position.z=0;pose();}}
      else {time=i/steps*clip.duration;root.position.z=time*speedMeters;pose();}
      root.updateMatrixWorld(true);mesh.skeleton.update();
      frames.push({t:contactIK?i/steps*contactIK.kinematics(speed).period:time/speed,phase:i/steps,distance:root.position.z,contact:contactState,soles:sampleSoles(mesh,solePatches)});
    }
    render();return {asset,rate:speed,steps,groundY:0,cycleDuration:contactIK?contactIK.kinematics(speed).period:clip.duration/speed,patches:solePatches,frames};
  },probe(indices){root.updateMatrixWorld(true);mesh.skeleton.update();return indices.map(i=>{mesh.getVertexPosition(i,v);return v.applyMatrix4(mesh.matrixWorld).toArray();});},setPhase(phase,view,draw=true){paused=true;time=phase*clip.duration;root.position.z=contactIK?phase*contactIK.kinematics(rate||1).stride:time*speedMeters;document.querySelector('#camera').value=view;if(contactIK)contactIK.reset(phase,root.position.z,rate);pose();return draw?render():sample();}};
  window.sRunReview.bodySample=bodySample;
  const bodyIds=[];
  for(let i=0;i<position.count;i++){
    let onlyBody=true;for(let j=0;j<4;j++)if(skinWeight.getComponent(i,j)>0&&/^(fore_|hind_)/.test(mesh.skeleton.bones[skinIndex.getComponent(i,j)].name))onlyBody=false;
    if(onlyBody)bodyIds.push(i);
  }
  window.sRunReview.bodyVertexIds=bodyIds.filter((_,i)=>i%Math.ceil(bodyIds.length/80)===0);
  window.sRunReview.bodyPhaseLead=bodyCoupling?.phaseLead||0;
  render();requestAnimationFrame(now=>{last=now;frame(now);});
}catch(error){document.querySelector('#error').textContent=String(error);canvas.dataset.error=String(error);throw error;}

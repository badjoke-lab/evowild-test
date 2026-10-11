import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const params=new URLSearchParams(location.search);
const renderer=new THREE.WebGLRenderer({canvas:document.querySelector('#review'),antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;
const scene=new THREE.Scene();scene.background=new THREE.Color('#788892');
const camera=new THREE.OrthographicCamera();camera.near=.1;camera.far=100;
scene.add(new THREE.HemisphereLight(0xddeaf4,0x494950,2.0));
function light(pos,power){const l=new THREE.DirectionalLight(0xfff5e9,power);l.position.set(...pos);scene.add(l);return l;}
const key=light([-4,7,5],3);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.5,far:20});key.shadow.bias=-.0003;key.shadow.normalBias=.035;
light([3,4,-5],1.8);light([4,5,4],1.2);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:0x64727a,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.015;floor.receiveShadow=true;scene.add(floor);
const views={SIDE:[0,2.1,10],FRONT:[-10,2,0],FRONT34:[-7,4.6,10],REAR34:[7,4,10],BACK:[10,2,0]};
let currentView=params.get('view')||'FRONT34',model,mixer,running=false,time=0,manual=false;
const status=document.querySelector('#status'),motionButton=document.querySelector('#motion');
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);const height=Math.max(4.7,5.9/(w/h));camera.left=-height*w/h/2;camera.right=height*w/h/2;camera.top=height/2;camera.bottom=-height/2;camera.updateProjectionMatrix();}
function setView(view){if(!views[view])throw Error(`Unknown view ${view}`);currentView=view;camera.position.set(...views[view]);camera.lookAt(-.02,1.48,0);document.querySelector('#viewLabel').textContent=`${view} · ${running?'minimal run study':'rest stance'}`;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));render();}
function render(){if(model)model.updateMatrixWorld(true);renderer.render(scene,camera);}
function setTime(seconds){manual=true;time=seconds;if(mixer)mixer.setTime(seconds);render();}
function setRunning(value){manual=false;running=value;if(mixer){if(running){mixer.clipAction(model.userData.runClip).play();}else{mixer.stopAllAction();model.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.pose();});}}motionButton.setAttribute('aria-pressed',String(running));setView(currentView);}
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>setView(b.dataset.view);
motionButton.onclick=()=>setRunning(!running);
window.addEventListener('resize',()=>{resize();render();});resize();setView(currentView);
const base=import.meta.env.BASE_URL;
const assetVersion=params.get('model')==='v3'?'v3':params.get('model')==='v2'?'v2':'v1';
const url=params.get('previous')==='1'?`${base}docs/evidence/p-canonical-3d-20261011/previous-proxy.glb`:`${base}models/evowild-p/p-canonical-${assetVersion}.glb`;
try{
 const gltf=await new GLTFLoader().loadAsync(url);model=gltf.scene;model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(model);
 if(gltf.animations.length){mixer=new THREE.AnimationMixer(model);model.userData.runClip=gltf.animations[0];}
 motionButton.disabled=!mixer;status.textContent=params.get('previous')==='1'?'Previous race proxy / rest geometry':`Canonical P ${assetVersion} / modeling review`;
 window.pReview={ready:true,setView,setTime,setRunning,render,model,silhouette:(value)=>{scene.overrideMaterial=value?new THREE.MeshBasicMaterial({color:0x172029}):null;floor.visible=!value;scene.background=new THREE.Color(value?'#ffffff':'#788892');render();},stats:()=>({view:currentView,triangles:renderer.info.render.triangles,drawCalls:renderer.info.render.calls,animations:gltf.animations.map(c=>c.name),bounds:new THREE.Box3().setFromObject(model).toJSON?.()})};
 setView(currentView);
}catch(e){status.textContent=`Model load failed: ${e.message}`;window.pReview={ready:false,error:String(e)};throw e;}
const clock=new THREE.Clock();function loop(){requestAnimationFrame(loop);const dt=clock.getDelta();if(running&&!manual){time+=Math.min(dt,.05);mixer?.setTime(time);render();}}loop();

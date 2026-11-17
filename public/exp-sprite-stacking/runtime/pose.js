import * as THREE from 'three';
import {createContactIK} from './s_contact_ik.js';
import {createAuthoredDrive} from './s_authored_drive.js';
import {createBodyCoupling} from './s_body_coupling.js';
import {selectSolePatches,sampleSoles} from './s_sole_metrics.js';
import {identifyFootSurfaces} from './s_foot_contact_geometry.js';
// Thin isolated adapter. Existing D3-C v2 modules above are byte-for-byte copies.
export function preparePose(gltf){
 const root=new THREE.Group(),model=gltf.scene;root.add(model);let mesh;
 model.updateMatrixWorld(true);let bounds=new THREE.Box3().setFromObject(model);
 model.scale.setScalar(2.85/(bounds.max.y-bounds.min.y));model.updateMatrixWorld(true);
 bounds=new THREE.Box3().setFromObject(model);const center=bounds.getCenter(new THREE.Vector3());
 model.position.set(-center.x,-bounds.min.y,-center.z);model.updateMatrixWorld(true);
 model.traverse(n=>{if(n.isSkinnedMesh)mesh=n;});if(!mesh)throw Error('Missing S skin');
 mesh.skeleton.update();const patches=selectSolePatches(mesh),surfaces=identifyFootSurfaces(mesh,patches);
 const ik=createContactIK(mesh,patches,{toeSurfaces:surfaces,continuousToe:true,toeRoundingWidth:.0015,foreReach:true});
 const clip=gltf.animations.find(a=>a.name==='EvoWild_S_Run_V5');
 const body=createBodyCoupling(mesh,clip,{smoothReturn:true,smoothNativeJoin:true,foreLoad:true});
 const drive=createAuthoredDrive(mesh,clip,gltf.animations.find(a=>a.name==='D3C_V2_Drive_Pose'));
 const mixer=new THREE.AnimationMixer(model);mixer.clipAction(clip).play();
 let time=0;function pose(){mixer.setTime(time);body.apply(time,1);drive.applyBody(time);root.updateMatrixWorld(true);ik.apply();ik.apply(drive.swingGuides(ik.limbs));root.updateMatrixWorld(true);mesh.skeleton.update();}
 function reset(){time=0;root.position.z=0;ik.reset(0,0,1);pose();}
 function advance(dt){const s=ik.advance(dt,1);time=s.cycles*clip.duration;root.position.z=s.distance;pose();}
 function localize(){root.position.z=0;root.updateMatrixWorld(true);mesh.skeleton.update();}
 reset();return {root,model,mesh,ik,clip,patches,reset,advance,localize,soles:()=>sampleSoles(mesh,patches),period:ik.kinematics(1).period,stride:ik.kinematics(1).stride};
}

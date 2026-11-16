import {Vector3,Quaternion,Euler} from 'three';

// Read-only review telemetry: actual skin points, not target coordinates.
export function sampleForeRecovery(mesh,surfaces,camera,distance,contact=null){
 mesh.updateWorldMatrix(true,false);mesh.skeleton.update();camera.updateMatrixWorld(true);
 const bones=new Map(mesh.skeleton.bones.map(b=>[b.name,b]));
 const world=b=>b.getWorldPosition(new Vector3());
 const chest=world(bones.get('chest'));
 const fore=surfaces.slice(0,2).map(surface=>{
  const chain=['upper','lower','foot'].map(n=>bones.get(surface.name+'_'+n));
  const joints=chain.map(world),points=surface.ids.map(i=>mesh.localToWorld(mesh.getVertexPosition(i,new Vector3())));
  const centroid=points.reduce((a,p)=>a.add(p),new Vector3()).multiplyScalar(1/points.length);
  const screen=points.map(p=>p.clone().project(camera));
  const bounds=[0,1].map(i=>[Math.min(...screen.map(p=>p.getComponent(i))),Math.max(...screen.map(p=>p.getComponent(i)))]);
  const jointPose=['scapula','upper','lower'].map(n=>{const b=bones.get(surface.name+'_'+n);return {name:b.name,localQuaternion:b.quaternion.toArray(),worldQuaternion:b.getWorldQuaternion(new Quaternion()).toArray(),localXDegrees:new Euler().setFromQuaternion(b.quaternion).x*180/Math.PI,position:world(b).toArray()};});
  return {name:surface.name,contact:contact?.limbs.find(l=>l.name===surface.name),jointPose,joints:joints.map(p=>p.toArray()),elbowDegrees:joints[0].clone().sub(joints[1]).angleTo(joints[2].clone().sub(joints[1]))*180/Math.PI,centroid:centroid.toArray(),relativeToChest:centroid.clone().sub(chest).toArray(),rootZ:centroid.z-distance,points:points.map(p=>p.toArray()),screenBoundsNdc:bounds};
 });
 const a=fore[0],b=fore[1],overlap=[0,1].map(i=>Math.max(0,Math.min(a.screenBoundsNdc[i][1],b.screenBoundsNdc[i][1])-Math.max(a.screenBoundsNdc[i][0],b.screenBoundsNdc[i][0])));
 return {chest:chest.toArray(),fore,centroidDistance:new Vector3().fromArray(a.centroid).distanceTo(new Vector3().fromArray(b.centroid)),nearestSurfaceDistance:Math.min(...a.points.flatMap(p=>b.points.map(q=>Math.hypot(...p.map((x,i)=>x-q[i]))))),screenOverlapAreaNdc:overlap[0]*overlap[1],screenHorizontalGapNdc:Math.max(0,Math.max(a.screenBoundsNdc[0][0],b.screenBoundsNdc[0][0])-Math.min(a.screenBoundsNdc[0][1],b.screenBoundsNdc[0][1]))};
}

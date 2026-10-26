import {Vector3,Quaternion} from 'three';
const up=new Vector3(0,1,0),forward=new Vector3(0,0,1);
const mod=x=>((x%1)+1)%1;
const smooth=x=>x*x*(3-2*x);
// Review-only locomotion. Rest geometry/joint positions are immutable v2.
// Root/chest/neck keep their native animation; only limb rotations are solved.
export function createContactIK(mesh,patches){
 const limbs=patches.map((patch,i)=>{
  const hind=patch.name.startsWith('hind'),names=['_upper','_lower','_foot',...(hind?['_toe']:[])];
  const bones=names.map(s=>mesh.skeleton.bones.find(b=>b.name===patch.name+s));
  const positions=bones.map(b=>b.getWorldPosition(new Vector3()));
  const rotations=bones.map(b=>b.getWorldQuaternion(new Quaternion()));
  const segments=positions.slice(1).map((p,i)=>p.clone().sub(positions[i]));
  const sole=patch.bindPoints.reduce((a,p)=>p[1]<a[1]?p:a,patch.bindPoints[0]);
  const point=patch.indices.map(i=>mesh.localToWorld(mesh.getVertexPosition(i,new Vector3()))).reduce((a,p)=>p.y<a.y?p:a);
  return {name:patch.name,hind,bones,rotations,segments,lengths:segments.map(s=>s.length()),soleOffset:point.clone().sub(positions.at(-1)),base:point,offset:[.64,.72,.15,.24][i],stance:hind?.23:.17};
 });
 function rotate(limb,index,direction){
  const bone=limb.bones[index],delta=new Quaternion().setFromUnitVectors(limb.segments[index].clone().normalize(),direction.clone().normalize());
  const world=delta.multiply(limb.rotations[index]);
  bone.quaternion.copy(bone.parent.getWorldQuaternion(new Quaternion()).invert().multiply(world));bone.updateWorldMatrix(false,true);
 }
 function twoBone(a,b,l1,l2){
  const direction=b.clone().sub(a),requested=direction.length(),d=Math.min(l1+l2-.0005,Math.max(Math.abs(l1-l2)+.0005,requested));direction.normalize();
  const pole=forward.clone().addScaledVector(direction,-forward.dot(direction)).normalize();
  const along=(l1*l1-l2*l2+d*d)/(2*d),height=Math.sqrt(Math.max(0,l1*l1-along*along));
  return {knee:a.clone().addScaledVector(direction,along).addScaledVector(pole,height),end:a.clone().addScaledVector(direction,d),reachError:Math.abs(requested-d)};
 }
 return {limbs,kinematics(rate){const cadence=2.4*Math.sqrt(Math.max(.01,rate));return {speed:4*rate,cadence,period:1/cadence,stride:4*rate/cadence};},apply(cycles,distance,rate){
  const k=this.kinematics(rate),diagnostics=[];
  mesh.updateWorldMatrix(true,false);
  for(const limb of limbs){
   const p=mod(cycles-limb.offset),span=k.stride*limb.stance;
   let z,y,stage;
   if(p<limb.stance){z=span/2-k.stride*p;y=0;stage=p<limb.stance*.55?'CONTACT':'PUSH';}
   else {const u=(p-limb.stance)/(1-limb.stance),d=-k.stride*(1-limb.stance);
    z=-span/2+span*smooth(u)+d*(u-3*u*u+2*u*u*u);
    y=(limb.hind?.48:.34)*Math.sin(Math.PI*u)**2;
    stage=u<.42?'RECOVERY':u<.58?'FLIGHT':'EXTENSION';
   }
   const target=new Vector3(limb.base.x,y,limb.base.z+distance+z+(limb.hind?.18:0));
   const end=target.clone().sub(limb.soleOffset),hip=limb.bones[0].getWorldPosition(new Vector3());
   let solved;
   if(limb.hind){
    // Retain hock-to-toe segment length and anatomical rear bend; solve knee
    // ahead of the hip/hock axis, never flip to the opposite IK solution.
    const distal=limb.segments[2].clone();
    const hock=end.clone().sub(distal);solved=twoBone(hip,hock,...limb.lengths);
    rotate(limb,0,solved.knee.clone().sub(hip));
    rotate(limb,1,solved.end.clone().sub(solved.knee));
    rotate(limb,2,distal);
   }else{
    solved=twoBone(hip,end,...limb.lengths);
    rotate(limb,0,solved.knee.clone().sub(hip));rotate(limb,1,solved.end.clone().sub(solved.knee));
   }
   const foot=limb.bones.at(-1);foot.quaternion.copy(foot.parent.getWorldQuaternion(new Quaternion()).invert().multiply(limb.rotations.at(-1)));foot.updateWorldMatrix(false,true);
   const joints=limb.bones.map(b=>b.getWorldPosition(new Vector3()));
   const angles=joints.slice(1,-1).map((p,j)=>joints[j].clone().sub(p).angleTo(joints[j+2].clone().sub(p))*180/Math.PI);
   diagnostics.push({name:limb.name,stage,phase:p,target:target.toArray(),reachError:solved.reachError,jointAngles:angles,joints:joints.map(p=>p.toArray())});
  }
  mesh.skeleton.update();return {cycles,...k,limbs:diagnostics};
 }};
}

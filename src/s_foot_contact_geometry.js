import {Vector3} from 'three';
// Spatial descriptors of this S mesh only. 'Rear' does not imply a human heel
// or an imported hoof joint. The immutable sculpt defines all selected IDs.
export function identifyFootSurfaces(mesh,patches){
 const {position,skinIndex,skinWeight}=mesh.geometry.attributes;
 return patches.map(patch=>{
  const hind=patch.name.startsWith('hind'),terminal=patch.name+(hind?'_toe':'_foot');
  const boneIndex=mesh.skeleton.bones.findIndex(b=>b.name===terminal),ids=[],guardIds=[],seen=new Set();
  for(let i=0;i<position.count;i++){
   const x=position.getX(i),y=position.getY(i),z=position.getZ(i);
   if(y>=-.70||(patch.name.endsWith('L')?x>=-.01945:x<=-.01945)||(hind?z>=-.6:z<=.1))continue;
   guardIds.push(i);if(y>=-.78)continue;
   const key=[x,y,z].map(v=>v.toFixed(6)).join(',');if(seen.has(key))continue;seen.add(key);ids.push(i);
  }
  const points=ids.map(i=>mesh.localToWorld(mesh.getVertexPosition(i,new Vector3())).toArray());
  const minY=Math.min(...points.map(p=>p[1])),surface=ids.filter((_,i)=>points[i][1]<=minY+.025);
  const low=surface.map(i=>({i,p:points[ids.indexOf(i)]})).sort((a,b)=>a.p[2]-b.p[2]);
  const count=Math.max(1,Math.ceil(low.length*.2)),rearIds=low.slice(0,count).map(p=>p.i),frontIds=low.slice(-count).map(p=>p.i);
  const pivotFor=degrees=>{const a=degrees*Math.PI/180;let k=0;for(let j=1;j<points.length;j++)if(points[j][1]*Math.cos(a)-points[j][2]*Math.sin(a)<points[k][1]*Math.cos(a)-points[k][2]*Math.sin(a))k=j;return ids[k];};
  const minTerminalWeight=Math.min(...ids.map(i=>{let w=0;for(let j=0;j<4;j++)if(skinIndex.getComponent(i,j)===boneIndex)w+=skinWeight.getComponent(i,j);return w;}));
  return {name:patch.name,hind,terminal,ids,guardIds,bindWorldPoints:points,rearIds,frontIds,flatPivot:pivotFor(0),sweep:[0,5,10,15,20,25,30,35].map(angle=>({angle,pivotId:pivotFor(angle)})),minTerminalWeight};
 });
}
export function sampleFootSurfaces(mesh,surfaces){
 return surfaces.map(s=>{
  const point=i=>mesh.localToWorld(mesh.getVertexPosition(i,new Vector3())).toArray();
  const mean=ids=>ids.map(point).reduce((a,p)=>a.map((v,i)=>v+p[i]/ids.length),[0,0,0]);
  const rear=mean(s.rearIds),front=mean(s.frontIds),points=s.ids.map(point);
  return {name:s.name,rear,front,pitchDegrees:Math.atan2(front[1]-rear[1],front[2]-rear[2])*180/Math.PI,minY:Math.min(...points.map(p=>p[1])),guardMinY:Math.min(...s.guardIds.map(i=>point(i)[1])),points};
 });
}

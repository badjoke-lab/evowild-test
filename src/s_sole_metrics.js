import {Vector3} from 'three';

// Select immutable mesh vertex IDs from the sole surface in bind geometry.
// No bone-weight group, joint origin, or animated centroid defines contact.
export function selectSolePatches(mesh){
  const pos=mesh.geometry.attributes.position, centerX=-.01945;
  return ['fore_L','fore_R','hind_L','hind_R'].map(name=>{
    const indices=[];
    for(let i=0;i<pos.count;i++){
      const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i);
      if(y<-.7 && (name.endsWith('_L')?x<centerX:x>centerX) && (name.startsWith('fore')?z>.1:z<-.6))indices.push(i);
    }
    const floor=Math.min(...indices.map(i=>pos.getY(i))), seen=new Set();
    const sole=indices.filter(i=>{
      if(pos.getY(i)>floor+.012)return false;
      const key=[pos.getX(i),pos.getY(i),pos.getZ(i)].map(n=>n.toFixed(6)).join(',');
      if(seen.has(key))return false;seen.add(key);return true;
    });
    if(sole.length<3)throw Error('No mesh sole patch: '+name);
    return {name,indices:sole,bindMinY:floor,bindPoints:sole.map(i=>[pos.getX(i),pos.getY(i),pos.getZ(i)])};
  });
}
export function sampleSoles(mesh,patches){
  const v=new Vector3();
  return patches.map(p=>{
    const points=p.indices.map(i=>{mesh.getVertexPosition(i,v);return v.applyMatrix4(mesh.matrixWorld).toArray();});
    let low=0;for(let i=1;i<points.length;i++)if(points[i][1]<points[low][1])low=i;
    return {name:p.name,points,minY:points[low][1],lowestVertex:p.indices[low],lowest:points[low]};
  });
}
export function summarizeSoles(frames,threshold=.025){
  const duration=frames.at(-1).t-frames[0].t;
  const feet=frames[0].soles.map((_,foot)=>{
    const rows=frames.map(f=>f.soles[foot]);let supportTime=0,contactTime=0,penetratingTime=0,slipZ=0,slipX=0,maxVertexSlip=0;
    const phases=[];
    for(let i=0;i<rows.length;i++){
      const row=rows[i],prev=rows[Math.max(0,i-1)],next=rows[Math.min(rows.length-1,i+1)];
      const vy=(next.minY-prev.minY)/Math.max(1e-9,frames[Math.min(rows.length-1,i+1)].t-frames[Math.max(0,i-1)].t);
      const vz=(next.lowest[2]-frames[Math.min(rows.length-1,i+1)].distance)-(prev.lowest[2]-frames[Math.max(0,i-1)].distance);
      const phase=row.minY<=threshold?(vz<0?'PUSH':'CONTACT'):(vy>.04?'RECOVERY':vy<-.04?'EXTENSION':'FLIGHT');
      phases.push({phase,penetrating:row.minY<0});
      if(!i)continue;
      const dt=frames[i].t-frames[i-1].t;
      if(row.minY<0)penetratingTime+=dt;
      if(Math.abs(row.minY)<=threshold)contactTime+=dt;
      if(row.minY<=threshold && prev.minY<=threshold){
        supportTime+=dt;let x=0,z=0;
        for(let k=0;k<row.points.length;k++){
          const dx=Math.abs(row.points[k][0]-prev.points[k][0]),dz=Math.abs(row.points[k][2]-prev.points[k][2]);
          x+=dx;z+=dz;maxVertexSlip=Math.max(maxVertexSlip,Math.hypot(dx,dz));
        }
        slipX+=x/row.points.length;slipZ+=z/row.points.length;
      }
    }
    return {name:rows[0].name,vertexCount:rows[0].points.length,minY:Math.min(...rows.map(r=>r.minY)),maxPenetration:Math.max(0,-Math.min(...rows.map(r=>r.minY))),
      recoveryHeight:Math.max(...rows.map(r=>r.minY)),supportCandidateTime:supportTime,validPlaneBandTime:contactTime,penetratingTime,
      supportSlipForward:slipZ,supportSlipLateral:slipX,maxVertexSlipPerStep:maxVertexSlip,phases};
  });
  return {duration,distance:frames.at(-1).distance-frames[0].distance,threshold,feet,
    interpretation:'Support candidate = sole minY <= 25mm, INCLUDING penetration so broken stance is not silently excluded. Slip sums per-vertex displacement (fixed IDs), not moving lowest-ID or weight centroid. Phases inferred from kinematics, not measured force.'};
}

// Additional B3 diagnostics. Keep the B1 support-band metric unchanged.
export function summarizeContactRun(trace){
 const summary=summarizeSoles(trace.frames),frames=trace.frames;
 return {...summary,cycleDuration:trace.cycleDuration,travelSpeed:summary.distance/summary.duration,cadence:1/summary.duration,stride:summary.distance,
  feet:summary.feet.map((foot,i)=>{
   const result={...foot,strictPlaneTime:0,strictPlaneSlipForward:0,strictPlaneSlipLateral:0,controllerStanceTime:0,controllerStanceSlipForward:0,controllerStanceSlipLateral:0,maxReachError:0,jointAngleRanges:[]};
   for(let j=0;j<frames.length;j++){
    const curr=frames[j],limb=curr.contact?.limbs[i];
    if(limb){result.maxReachError=Math.max(result.maxReachError,limb.reachError);limb.jointAngles.forEach((a,k)=>{const r=result.jointAngleRanges[k]||[Infinity,-Infinity];r[0]=Math.min(r[0],a);r[1]=Math.max(r[1],a);result.jointAngleRanges[k]=r;});}
    if(!j)continue;
    const prev=frames[j-1],a=prev.soles[i],b=curr.soles[i],dt=curr.t-prev.t;
    const states=['CONTACT','PUSH'];
    for(const [name,active] of [['strictPlane',Math.abs(a.minY)<=.001&&Math.abs(b.minY)<=.001],['controllerStance',limb&&states.includes(limb.stage)&&states.includes(prev.contact.limbs[i].stage)]]){
     if(!active)continue;result[name+'Time']+=dt;
     for(let k=0;k<b.points.length;k++){
      result[name+'SlipForward']+=Math.abs(b.points[k][2]-a.points[k][2])/b.points.length;
      result[name+'SlipLateral']+=Math.abs(b.points[k][0]-a.points[k][0])/b.points.length;
     }
    }
   }
   if(!frames[0].contact){for(const key of ['controllerStanceTime','controllerStanceSlipForward','controllerStanceSlipLateral','maxReachError'])result[key]=null;}
   return result;
  })};
}

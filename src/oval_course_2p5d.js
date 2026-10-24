// EvoWild Run / 2.5D racetrack world geometry.
// Exact 1600m oval: two 500m straights and two 300m half-turns.
// Rendering uses the same continuous race distance and lane state as simulation.
export const OVAL_DISTANCE = 1600;
export const OVAL_STRAIGHT = 500;
export const OVAL_HALF_TURN = 300;
export const OVAL_RADIUS = OVAL_HALF_TURN / Math.PI;
export const OVAL_LANE_WIDTH = 3.2;
const TAU = Math.PI*2;
export function wrapOvalDistance(m) {
  if(!Number.isFinite(m)) return 0;
  return ((m%OVAL_DISTANCE)+OVAL_DISTANCE)%OVAL_DISTANCE;
}
export function ovalWorld(m, lane=1.5) {
  const d=wrapOvalDistance(m);
  let x,z,tx,tz;
  if(d<500) {
    x=-250+d; z=-OVAL_RADIUS; tx=1;tz=0;
  }else if(d<800) {
    const theta=-Math.PI/2+(d-500)/OVAL_RADIUS;
    x=250+OVAL_RADIUS*Math.cos(theta);
    z=OVAL_RADIUS*Math.sin(theta);
    tx=-Math.sin(theta);tz=Math.cos(theta);
  }else if(d<1300) {
    x=250-(d-800);z=OVAL_RADIUS;tx=-1;tz=0;
  }else{
    const theta=Math.PI/2+(d-1300)/OVAL_RADIUS;
    x=-250+OVAL_RADIUS*Math.cos(theta);
    z=OVAL_RADIUS*Math.sin(theta);
    tx=-Math.sin(theta);tz=Math.cos(theta);
  }
  // Lower lane index means inside, always on left side of the tangent.
  const lateral=(1.5-lane)*OVAL_LANE_WIDTH;
  return {x:x-tz*lateral,z:z+tx*lateral,tx,tz,heading:Math.atan2(tz,tx)};
}
export function ovalChaseCamera(m, lane=1.5) {
  const c=ovalWorld(m,lane);
  const eyeX=c.x-c.tx*54+c.tz*13;
  const eyeZ=c.z-c.tz*54-c.tx*13;
  const dx=c.x-eyeX, dz=c.z-eyeZ;
  const length=Math.hypot(dx,dz);
  const fx=dx/length,fz=dz/length;
  return {eyeX,eyeZ,fx,fz,rx:fz,rz:-fx,horizon:0.29,eyeHeight:17};
}
export function projectOval(camera,p,width,height,elevation=0) {
  const dx=p.x-camera.eyeX,dz=p.z-camera.eyeZ;
  const depth=dx*camera.fx+dz*camera.fz;
  const side=dx*camera.rx+dz*camera.rz;
  if(depth<=3)return null;
  const focalX=Math.min(width*1.32,height*1.65);
  const focalY=height*1.28;
  return {
    x:width*.5+side*focalX/depth,
    y:height*camera.horizon+(camera.eyeHeight-elevation)*focalY/depth,
    depth,
    scale:focalY/depth
  };
}
export function projectOvalRunner(camera,m,lane,width,height) {
  return projectOval(camera,ovalWorld(m,lane),width,height);
}
export function ovalSegmentAt(m) {
  const d=wrapOvalDistance(m);
  if(d<500)return "HOME_STRAIGHT";
  if(d<800)return "FIRST_TURN";
  if(d<1300)return "BACK_STRAIGHT";
  return "FINAL_TURN";
}
export function ovalMinimapPoint(m, x,y,w,h) {
  const world=ovalWorld(m,1.5);
  const rx=OVAL_RADIUS+14;
  return {
    x:x+(world.x+250+OVAL_RADIUS)/(500+2*OVAL_RADIUS)*w,
    y:y+(world.z+rx)/(2*rx)*h
  };
}

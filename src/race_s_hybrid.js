import * as THREE from "three";

const canvas=document.querySelector("#raceCanvas");
const stage=document.querySelector("#stage");
const ui={
  rank:document.querySelector("#rank"),
  speed:document.querySelector("#speed"),
  command:document.querySelector("#command"),
  reason:document.querySelector("#reason"),
  distance:document.querySelector("#distance"),
  clock:document.querySelector("#clock"),
  progress:document.querySelector("#progress"),
  ranking:document.querySelector("#ranking"),
  countdown:document.querySelector("#countdown"),
  pause:document.querySelector("#pause"),
  reset:document.querySelector("#reset"),
  assetStatus:document.querySelector("#assetStatus")
};

const BASE=import.meta.env.BASE_URL||"/";
const FIELD_SIZE=8;
const SELECTED_ID=1;
const RACE_METERS=1440;
const WORLD_SCALE=.08;
const ROAD_HALF=6.4;
const LANES=[1,1,2,3,0,2,1,3];
const CRUISE=[32.6,29.6,31.1,30.0,31.5,29.9,30.6,30.2];
const ACCEL=[12.2,10.3,11.2,10.6,11.0,10.2,10.8,10.4];
const NAMES=["Mica","Vela","Rook","Serein","Flint","Nacre","Ilex","Sora"];
const S_FRAMES=[
  {phase:"CONTACT",col:0,row:0,y:0},
  {phase:"PUSH",col:1,row:0,y:0},
  {phase:"LIFT",col:2,row:0,y:0},
  {phase:"FLIGHT",col:0,row:1,y:-.42},
  {phase:"REACH",col:1,row:1,y:-.17},
  {phase:"LAND",col:2,row:1,y:-.16}
];

const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const up=new THREE.Vector3(0,1,0);
const scratchA=new THREE.Vector3();
const scratchB=new THREE.Vector3();
const scratchSide=new THREE.Vector3();
const cameraLook=new THREE.Vector3();

let renderer;
try{
  renderer=new THREE.WebGLRenderer({
    canvas,
    antialias:innerWidth>700,
    powerPreference:"high-performance",
    precision:"mediump"
  });
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.08;
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,innerWidth<700?1.25:1.35));
  stage.dataset.webglReady="true";
}catch(error){
  stage.dataset.webglReady="error";
  ui.assetStatus.textContent="WebGL renderer failed";
  throw error;
}

const scene=new THREE.Scene();
scene.background=new THREE.Color(0x9db7c2);
scene.fog=new THREE.Fog(0x9db7c2,24,76);

const camera=new THREE.PerspectiveCamera(42,1,.1,160);
camera.position.set(0,8,15);
scene.add(camera);

scene.add(new THREE.HemisphereLight(0xe7f3ff,0x18231d,1.18));
const sun=new THREE.DirectionalLight(0xffefd0,1.72);
sun.position.set(26,34,18);
scene.add(sun);
const rim=new THREE.DirectionalLight(0x72cfff,.65);
rim.position.set(-18,13,-20);
scene.add(rim);

function courseY(m){
  return (
    Math.sin(m*.0105)*.76+
    Math.sin(m*.0034+.8)*1.10+
    (m>260&&m<520?Math.sin((m-260)/260*Math.PI)*1.45:0)-
    (m>770&&m<1040?Math.sin((m-770)/270*Math.PI)*1.05:0)
  );
}

function courseZ(m){
  return (
    Math.sin(m*.0062)*4.4+
    Math.sin(m*.00215+1.1)*3.4+
    (m>520&&m<820?Math.sin((m-520)/300*Math.PI)*2.6:0)
  );
}

function trackPoint(m,target=new THREE.Vector3()){
  return target.set(m*WORLD_SCALE,courseY(m),courseZ(m));
}

function tangentAt(m,target=new THREE.Vector3()){
  trackPoint(clamp(m-1,0,RACE_METERS),scratchA);
  trackPoint(clamp(m+1,0,RACE_METERS),scratchB);
  return target.copy(scratchB).sub(scratchA).normalize();
}

function sideAt(m,target=new THREE.Vector3()){
  const t=tangentAt(m,scratchA);
  target.set(-t.z,0,t.x);
  if(target.lengthSq()<.001) target.set(0,0,1);
  return target.normalize();
}

function laneOffsetWorld(lane){
  return lerp(-ROAD_HALF*.68,ROAD_HALF*.68,clamp(lane/3,0,1));
}

function buildTrack(){
  const samples=420;
  const verts=[];
  const uv=[];
  const indices=[];

  for(let i=0;i<=samples;i++){
    const m=RACE_METERS*i/samples;
    const p=trackPoint(m,new THREE.Vector3());
    const side=sideAt(m,new THREE.Vector3());
    for(const offset of [-ROAD_HALF,ROAD_HALF]){
      const q=p.clone().addScaledVector(side,offset);
      verts.push(q.x,q.y,q.z);
      uv.push(i/samples,offset<0?0:1);
    }
  }
  for(let i=0;i<samples;i++){
    const a=i*2,b=a+1,c=a+2,d=a+3;
    indices.push(a,c,b,b,c,d);
  }

  const geo=new THREE.BufferGeometry();
  geo.setAttribute("position",new THREE.Float32BufferAttribute(verts,3));
  geo.setAttribute("uv",new THREE.Float32BufferAttribute(uv,2));
  geo.setIndex(indices);
  geo.computeVertexNormals();

  const mat=new THREE.MeshStandardMaterial({
    color:0x242b30,
    roughness:.80,
    metalness:.09
  });
  const road=new THREE.Mesh(geo,mat);
  road.receiveShadow=false;
  scene.add(road);

  const dashMat=new THREE.LineBasicMaterial({
    color:0xcbd7d9,
    transparent:true,
    opacity:.28
  });
  const edgeMat=new THREE.LineBasicMaterial({
    color:0x78def4,
    transparent:true,
    opacity:.80
  });

  function dashedOffset(offset,material,dash=8,gap=6){
    const positions=[];
    for(let m=0;m<RACE_METERS;m+=dash+gap){
      const a=trackPoint(m,new THREE.Vector3());
      const b=trackPoint(Math.min(RACE_METERS,m+dash),new THREE.Vector3());
      a.addScaledVector(sideAt(m,new THREE.Vector3()),offset).y+=.035;
      b.addScaledVector(sideAt(Math.min(RACE_METERS,m+dash),new THREE.Vector3()),offset).y+=.035;
      positions.push(a.x,a.y,a.z,b.x,b.y,b.z);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));
    scene.add(new THREE.LineSegments(g,material));
  }

  for(const offset of [-ROAD_HALF*.34,0,ROAD_HALF*.34]) dashedOffset(offset,dashMat,5,5);
  dashedOffset(-ROAD_HALF+.05,edgeMat,9,1);
  dashedOffset(ROAD_HALF-.05,edgeMat,9,1);
}
buildTrack();

const ground=new THREE.Mesh(
  new THREE.PlaneGeometry(RACE_METERS*WORLD_SCALE+45,120),
  new THREE.MeshStandardMaterial({color:0x314a38,roughness:1})
);
ground.rotation.x=-Math.PI/2;
ground.position.set(RACE_METERS*WORLD_SCALE*.5,-2.7,0);
scene.add(ground);

function buildTracksideStructures(){
  const count=64;
  const bodyGeo=new THREE.BoxGeometry(.54,3.4,1.05);
  const lightGeo=new THREE.BoxGeometry(.58,.12,1.10);
  const bodyMat=new THREE.MeshStandardMaterial({
    color:0x182529,
    roughness:.68,
    metalness:.26
  });
  const lightMat=new THREE.MeshStandardMaterial({
    color:0x65d7ef,
    emissive:0x176579,
    emissiveIntensity:1.65,
    roughness:.35
  });
  const bodies=new THREE.InstancedMesh(bodyGeo,bodyMat,count);
  const lights=new THREE.InstancedMesh(lightGeo,lightMat,count);
  const matrix=new THREE.Matrix4();
  const quat=new THREE.Quaternion();
  const pos=new THREE.Vector3();
  const scale=new THREE.Vector3();

  for(let i=0;i<count;i++){
    const m=30+i*(RACE_METERS-60)/(count-1);
    const p=trackPoint(m,new THREE.Vector3());
    const side=sideAt(m,new THREE.Vector3());
    const seed=(Math.sin(i*17.371)*.5+.5);
    const sign=i%2===0?1:-1;
    const offset=sign*(10.5+seed*7.5);
    pos.copy(p).addScaledVector(side,offset);
    const h=.70+seed*.85;
    pos.y+=1.7*h-.35;
    const yaw=Math.atan2(side.x,side.z)+(sign<0?Math.PI:0);
    quat.setFromAxisAngle(up,yaw+.15*Math.sin(i*.7));
    scale.set(1,h,1);
    matrix.compose(pos,quat,scale);
    bodies.setMatrixAt(i,matrix);

    const capPos=pos.clone();
    capPos.y+=1.63*h;
    matrix.compose(capPos,quat,scale.set(1,1,1));
    lights.setMatrixAt(i,matrix);
  }
  scene.add(bodies,lights);
}
buildTracksideStructures();

function buildFence(){
  const marks=[];
  for(let m=0;m<=RACE_METERS;m+=16){
    for(const sign of [-1,1])marks.push([m,sign]);
  }
  const postGeo=new THREE.BoxGeometry(.18,1.08,.18);
  const capGeo=new THREE.BoxGeometry(.24,.10,.24);
  const postMat=new THREE.MeshStandardMaterial({color:0x17262a,roughness:.72,metalness:.18});
  const capMat=new THREE.MeshStandardMaterial({
    color:0x76def2,
    emissive:0x155a6c,
    emissiveIntensity:1.45,
    roughness:.38
  });
  const posts=new THREE.InstancedMesh(postGeo,postMat,marks.length);
  const caps=new THREE.InstancedMesh(capGeo,capMat,marks.length);
  const matrix=new THREE.Matrix4();
  marks.forEach(([m,sign],i)=>{
    const p=trackPoint(m,new THREE.Vector3());
    p.addScaledVector(sideAt(m,new THREE.Vector3()),sign*(ROAD_HALF+.70));
    p.y+=.53;
    matrix.makeTranslation(p.x,p.y,p.z);
    posts.setMatrixAt(i,matrix);
    p.y+=.59;
    matrix.makeTranslation(p.x,p.y,p.z);
    caps.setMatrixAt(i,matrix);
  });
  scene.add(posts,caps);
}
buildFence();

function buildSectorGates(){
  for(let m=240;m<RACE_METERS;m+=240){
    const group=new THREE.Group();
    const p=trackPoint(m,new THREE.Vector3());
    const tangent=tangentAt(m,new THREE.Vector3());
    const yaw=-Math.atan2(tangent.z,tangent.x);
    group.position.copy(p);
    group.rotation.y=yaw;

    const mat=new THREE.MeshStandardMaterial({color:0x17272e,roughness:.65,metalness:.22});
    const accent=new THREE.MeshStandardMaterial({color:0x7bdcf4,emissive:0x17495a,roughness:.55});
    const left=new THREE.Mesh(new THREE.BoxGeometry(.28,4.2,.28),mat);
    const right=left.clone();
    left.position.set(0,2.1,-ROAD_HALF-.35);
    right.position.set(0,2.1,ROAD_HALF+.35);
    const top=new THREE.Mesh(new THREE.BoxGeometry(.32,.38,ROAD_HALF*2+.98),mat);
    top.position.set(0,4.05,0);
    const strip=new THREE.Mesh(new THREE.BoxGeometry(.34,.08,ROAD_HALF*2+.98),accent);
    strip.position.set(-.02,4.26,0);
    group.add(left,right,top,strip);
    scene.add(group);
  }
}
buildSectorGates();

function makeRacers(){
  return Array.from({length:FIELD_SIZE},(_,i)=>({
    id:i+1,
    name:NAMES[i],
    distance:i*5.2,
    speed:0,
    cruise:CRUISE[i],
    accel:ACCEL[i],
    stamina:100,
    lane:LANES[i],
    targetLane:LANES[i],
    phaseOffset:i*.87,
    cooldown:0,
    command:"HOLD FORM",
    reason:"Pre-start",
    finished:false,
    finishPlace:0,
    finishTime:0,
    visual:null,
    shadow:null,
    ring:null,
    lastFrame:-1
  }));
}
let racers=makeRacers();

const selected=()=>racers.find(r=>r.id===SELECTED_ID);
const order=()=>[...racers].sort((a,b)=>{
  if(a.finished&&b.finished)return a.finishPlace-b.finishPlace;
  if(a.finished)return -1;
  if(b.finished)return 1;
  return b.distance-a.distance;
});
const rankOf=r=>order().findIndex(x=>x===r)+1;

function occupiedNear(r,lane,radius=8.5){
  return racers.some(o=>o!==r&&!o.finished&&Math.abs(o.lane-lane)<.28&&Math.abs(o.distance-r.distance)<radius);
}
function gapAhead(r){
  let best=Infinity;
  for(const o of racers){
    if(o===r||o.finished||Math.abs(o.lane-r.lane)>.34)continue;
    const g=o.distance-r.distance;
    if(g>0&&g<best)best=g;
  }
  return best;
}
function chooseLane(r){
  const candidates=[r.lane-1,r.lane+1,r.lane-2,r.lane+2]
    .filter(l=>l>=0&&l<=3&&!occupiedNear(r,l,9))
    .sort((a,b)=>Math.abs(a-r.lane)-Math.abs(b-r.lane));
  return candidates[0]??r.lane;
}
function targetSpeedFor(r){
  const p=r.distance/RACE_METERS;
  let target=r.cruise*(p<.15?1.035:p>.87?1.085:p>.68?1.025:1);
  const gap=gapAhead(r);
  if(gap<7.5&&r.cooldown<=0){
    const next=chooseLane(r);
    if(next!==r.lane){
      r.targetLane=next;
      r.cooldown=1500;
      r.command="SHIFT LINE";
      r.reason="Traffic ahead";
      target*=1.015;
    }else{
      target*=clamp(gap/7.5,.77,.97);
      r.command="HOLD GAP";
      r.reason="Blocked";
    }
  }else if(p>.87&&r.stamina>22){
    r.command="COMMIT";
    r.reason="Final drive";
  }else if(p>.68){
    r.command="PRESS";
    r.reason="Build phase";
  }else{
    r.command="HOLD FORM";
    r.reason="Efficient pace";
  }
  if(r.stamina<18){
    target*=.89;
    r.command="PRESERVE";
    r.reason="Low stamina";
  }
  return target*(.83+.17*(r.stamina/100));
}

let elapsed=0;
let countdownRemaining=2500;
let raceState="countdown";
let paused=false;
let finishCounter=0;
let last=performance.now();
let frameCounter=0;
let lastRankingPaint=0;

function updateRace(dtMs){
  if(paused)return;
  const dt=Math.min(50,dtMs)/1000;
  if(raceState==="countdown"){
    countdownRemaining-=dtMs;
    const n=Math.ceil(countdownRemaining/800);
    ui.countdown.hidden=false;
    ui.countdown.textContent=n>0?String(n):"GO";
    if(countdownRemaining<=0){
      raceState="running";
      stage.dataset.raceState="running";
      ui.countdown.textContent="GO";
    }
    return;
  }
  if(raceState!=="running")return;
  elapsed+=dtMs;
  if(elapsed>650)ui.countdown.hidden=true;

  for(const r of racers){
    if(r.finished)continue;
    r.cooldown=Math.max(0,r.cooldown-dtMs);
    let target=targetSpeedFor(r)+Math.sin(elapsed*.0015+r.id*1.51)*.16;
    const diff=target-r.speed;
    const step=r.accel*dt*(diff>=0?1:1.45);
    r.speed+=clamp(diff,-step,step);
    if(Math.abs(r.lane-r.targetLane)>.001){
      const dir=Math.sign(r.targetLane-r.lane);
      const next=r.lane+dir*dt*1.9;
      r.lane=(dir>0?next>=r.targetLane:next<=r.targetLane)?r.targetLane:next;
    }
    const effort=Math.max(0,r.speed/r.cruise-.95);
    r.stamina=Math.max(0,r.stamina-(.62+effort*effort*4.4)*dt);
    r.distance+=Math.max(0,r.speed)*dt;
    if(r.distance>=RACE_METERS){
      r.distance=RACE_METERS;
      r.finished=true;
      r.finishPlace=++finishCounter;
      r.finishTime=elapsed;
    }
  }
  if(finishCounter===racers.length){
    raceState="finished";
    stage.dataset.raceState="finished";
  }
}

const spriteSheet=new Image();
spriteSheet.decoding="async";
spriteSheet.src=BASE+"concept/s-run-sheet.webp";

function makeVisual(r){
  const c=document.createElement("canvas");
  c.width=384;
  c.height=256;
  const cctx=c.getContext("2d");
  const tex=new THREE.CanvasTexture(c);
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.minFilter=THREE.LinearFilter;
  tex.magFilter=THREE.LinearFilter;
  const mat=new THREE.SpriteMaterial({
    map:tex,
    transparent:true,
    depthTest:true,
    depthWrite:false,
    alphaTest:.035,
    color:r.id===SELECTED_ID?0xdff9ff:0xffffff
  });
  const sprite=new THREE.Sprite(mat);
  sprite.center.set(.5,.22);
  scene.add(sprite);

  const shadow=new THREE.Mesh(
    new THREE.CircleGeometry(1,24),
    new THREE.MeshBasicMaterial({color:0x061014,transparent:true,opacity:.28,depthWrite:false})
  );
  shadow.rotation.x=-Math.PI/2;
  scene.add(shadow);

  let ring=null;
  if(r.id===SELECTED_ID){
    ring=new THREE.Mesh(
      new THREE.RingGeometry(1.2,1.42,32),
      new THREE.MeshBasicMaterial({color:0x6cdef5,transparent:true,opacity:.42,side:THREE.DoubleSide,depthWrite:false})
    );
    ring.rotation.x=-Math.PI/2;
    scene.add(ring);
  }

  r.visual={canvas:c,ctx:cctx,texture:tex,sprite};
  r.shadow=shadow;
  r.ring=ring;
}

function drawSpriteFrame(r,frameIndex){
  if(!r.visual||r.lastFrame===frameIndex||!spriteSheet.naturalWidth)return;
  r.lastFrame=frameIndex;
  const fw=spriteSheet.naturalWidth/3;
  const fh=spriteSheet.naturalHeight/2;
  const frame=S_FRAMES[frameIndex];
  const {canvas:c,ctx:cctx,texture}=r.visual;
  cctx.clearRect(0,0,c.width,c.height);
  cctx.drawImage(spriteSheet,frame.col*fw,frame.row*fh,fw,fh,0,0,c.width,c.height);
  texture.needsUpdate=true;

  const aspect=fw/fh;
  const h=innerWidth<700?2.5:2.8;
  r.visual.sprite.scale.set(h*aspect,h,1);
}

spriteSheet.onload=()=>{
  racers.forEach(makeVisual);
  racers.forEach((r,i)=>drawSpriteFrame(r,i%6));
  stage.dataset.sRunSheet="ready";
  ui.assetStatus.textContent="S run cycle ready";
};
spriteSheet.onerror=()=>{
  stage.dataset.sRunSheet="error";
  ui.assetStatus.textContent="S run cycle failed";
};

function updateVisuals(){
  for(const r of racers){
    if(!r.visual)continue;
    const p=trackPoint(r.distance,new THREE.Vector3());
    const side=sideAt(r.distance,new THREE.Vector3());
    const laneOffset=laneOffsetWorld(r.lane);
    p.addScaledVector(side,laneOffset);

    const cadence=7+clamp(r.speed/31.5,0,1)*8.2;
    const frameFloat=elapsed/1000*cadence+r.phaseOffset;
    const frameIndex=((Math.floor(frameFloat)%6)+6)%6;
    const frame=S_FRAMES[frameIndex];
    drawSpriteFrame(r,frameIndex);

    const fw=spriteSheet.naturalWidth/3;
    const fh=spriteSheet.naturalHeight/2;
    const aspect=fw/fh;
    const spriteH=(innerWidth<700?2.55:2.9)*(r.id===SELECTED_ID?1.06:1);
    r.visual.sprite.scale.set(spriteH*aspect,spriteH,1);

    const flight=frame.phase==="FLIGHT"?1:frame.phase==="REACH"?.55:frame.phase==="LIFT"?.25:0;
    r.visual.sprite.position.set(p.x,p.y+.42+flight*.14,p.z);

    r.shadow.position.set(p.x,p.y+.045,p.z);
    const shadowScale=flight?.82:1.0;
    r.shadow.scale.set(1.18*shadowScale,.42*shadowScale,1);
    r.shadow.material.opacity=.30-flight*.13;

    if(r.ring){
      r.ring.position.set(p.x,p.y+.055,p.z);
      const pulse=1+Math.sin(elapsed*.008)*.06;
      r.ring.scale.setScalar(pulse);
    }

    if(r.id===SELECTED_ID){
      stage.dataset.sRunFrame=String(frameIndex);
      stage.dataset.sRunPhase=frame.phase;
      stage.dataset.selectedWorldX=p.x.toFixed(2);
      stage.dataset.selectedWorldZ=p.z.toFixed(2);
    }
  }
}

function updateCamera(){
  const focus=selected();
  const p=trackPoint(focus.distance,new THREE.Vector3());
  const t=tangentAt(focus.distance,new THREE.Vector3());
  const side=sideAt(focus.distance,new THREE.Vector3());

  const mobile=innerWidth<700;
  const desired=p.clone()
    .addScaledVector(side,mobile?11.2:12.4)
    .addScaledVector(t,-3.8)
    .add(new THREE.Vector3(0,mobile?5.3:5.5,0));

  const speedNorm=clamp(focus.speed/31.5,0,1);
  const shake=(speedNorm>.72?(speedNorm-.72)*.09:0);
  desired.x+=Math.sin(elapsed*.041)*shake;
  desired.y+=Math.sin(elapsed*.053+1.2)*shake*.45;

  camera.position.lerp(desired,mobile?.14:.10);

  const look=p.clone().addScaledVector(t,5.4).add(new THREE.Vector3(0,.82,0));
  cameraLook.lerp(look,.12);
  camera.lookAt(cameraLook);

  const targetFov=(mobile?43:38)+speedNorm*4.2;
  camera.fov=lerp(camera.fov,targetFov,.08);
  camera.updateProjectionMatrix();

  stage.dataset.cameraDistance=camera.position.distanceTo(p).toFixed(2);
  stage.dataset.hybridCamera="side-chase";
}

function fmtTime(ms){
  const t=Math.max(0,ms)/1000;
  const min=Math.floor(t/60),sec=Math.floor(t%60),cs=Math.floor((t%1)*100);
  return `${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}

function updateUI(now){
  const focus=selected();
  const ranks=order();
  ui.rank.textContent=`${rankOf(focus)} / ${FIELD_SIZE}`;
  ui.speed.textContent=String(Math.round(focus.speed*3.6));
  ui.command.textContent=focus.command;
  ui.reason.textContent=focus.reason;
  ui.distance.textContent=`${Math.round(focus.distance)} / ${RACE_METERS} m`;
  ui.clock.textContent=fmtTime(elapsed);
  ui.progress.style.width=`${clamp(focus.distance/RACE_METERS*100,0,100).toFixed(2)}%`;

  if(now-lastRankingPaint>180){
    lastRankingPaint=now;
    ui.ranking.innerHTML=ranks.map((r,i)=>
      `<span class="${r.id===SELECTED_ID?"selected":""}">#${i+1} S${String(r.id).padStart(2,"0")}</span>`
    ).join("");
  }

  stage.dataset.selectedDistance=focus.distance.toFixed(2);
  stage.dataset.selectedSpeed=focus.speed.toFixed(2);
  stage.dataset.selectedRank=String(rankOf(focus));
  stage.dataset.frameCounter=String(frameCounter);
}

function resize(){
  const rect=canvas.getBoundingClientRect();
  const w=Math.max(320,Math.floor(rect.width));
  const h=Math.max(420,Math.floor(rect.height));
  renderer.setSize(w,h,false);
  camera.aspect=w/h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);
resize();

function resetRace(){
  const old=racers;
  old.forEach(r=>{
    if(r.visual){
      scene.remove(r.visual.sprite);
      r.visual.texture.dispose();
      r.visual.sprite.material.dispose();
    }
    if(r.shadow)scene.remove(r.shadow);
    if(r.ring)scene.remove(r.ring);
  });
  racers=makeRacers();
  if(spriteSheet.naturalWidth) racers.forEach(makeVisual);
  elapsed=0;
  countdownRemaining=2500;
  raceState="countdown";
  finishCounter=0;
  paused=false;
  ui.pause.textContent="Pause";
  ui.countdown.hidden=false;
  ui.countdown.textContent="3";
  stage.dataset.raceState="countdown";
}
ui.pause.addEventListener("click",()=>{
  paused=!paused;
  ui.pause.textContent=paused?"Resume":"Pause";
});
ui.reset.addEventListener("click",resetRace);

stage.dataset.raceState="countdown";
ui.assetStatus.textContent="Loading S run cycle…";

function frame(now){
  const rawDt=Math.max(0,now-last);
  last=now;
  updateRace(rawDt);
  updateVisuals();
  updateCamera();
  renderer.render(scene,camera);
  frameCounter++;
  updateUI(now);
  requestAnimationFrame(frame);
}
requestAnimationFrame(now=>{
  last=now;
  frame(now);
});

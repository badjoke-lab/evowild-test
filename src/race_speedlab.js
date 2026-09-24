const canvas = document.querySelector("#speedlabCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#speedlabStage");
const rankbox = document.querySelector("#rankbox");
const assetState = document.querySelector("#assetState");

const ui = {
  section: document.querySelector("#section"),
  clock: document.querySelector("#clock"),
  distance: document.querySelector("#distance"),
  selectedMorph: document.querySelector("#selectedMorph"),
  selectedName: document.querySelector("#selectedName"),
  selectedSpeed: document.querySelector("#selectedSpeed"),
  selectedRank: document.querySelector("#selectedRank")
};

const BASE = import.meta.env.BASE_URL || "/";
const RACE_METERS = 1200;
const LANES = 6;
const SELECTED_ID = 1;

const MORPHS = {
  S: { sheet: "s-run-sheet.svg", cruise: 20.6, accel: 5.4, drain: 1.06, w: 214, h: 178, phase: 0.00 },
  P: { sheet: "p-run-sheet.svg", cruise: 19.8, accel: 6.2, drain: 1.12, w: 226, h: 190, phase: 0.90 },
  E: { sheet: "e-run-sheet.svg", cruise: 19.3, accel: 4.5, drain: 0.82, w: 218, h: 186, phase: 1.80 },
  A: { sheet: "a-run-sheet.svg", cruise: 20.0, accel: 5.3, drain: 0.94, w: 224, h: 176, phase: 2.70 }
};

const names = ["Vela","Brim","Serein","Kite","Aster","Mica","Rook","Nacre","Ilex","Lumen","Dune","Tern"];
const cycle = ["S","P","E","A"];
const sheets = new Map();

function loadSheet(morph) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => { sheets.set(morph, img); resolve(); };
    img.onerror = reject;
    img.src = BASE + "concept/" + MORPHS[morph].sheet;
  });
}

Promise.all(Object.keys(MORPHS).map(loadSheet)).then(() => {
  stage.dataset.state = "ready";
  stage.dataset.motion = "sprite-sheets";
  assetState.textContent = "S / P / E / A dedicated run sheets loaded";
}).catch((error) => {
  stage.dataset.state = "asset-error";
  assetState.textContent = "Run sheet load failed";
  console.error(error);
});

let width = 1280;
let height = 720;
let dpr = 1;

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, rect.width);
  height = Math.max(480, rect.height);
  dpr = Math.min(window.devicePixelRatio || 1, 1.65);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function makeRacers() {
  return names.map((name, index) => {
    const morph = cycle[index % cycle.length];
    const m = MORPHS[morph];
    return {
      id: index + 1,
      name,
      morph,
      lane: index % LANES,
      laneF: index % LANES,
      distance: Math.max(0, 32 - index * 2.25),
      speed: 0,
      stamina: 100,
      cruise: m.cruise + ((index * 11) % 5) * 0.11,
      accel: m.accel,
      drain: m.drain,
      cooldown: 0,
      seed: index * 1.731 + m.phase,
      command: "BUILD"
    };
  });
}

let racers = makeRacers();
let elapsed = 0;
let last = performance.now();
let cameraMode = "chase";
let lastRankPaint = 0;
const particles = Array.from({ length: 120 }, () => ({ active:false, x:0,y:0,vx:0,vy:0,life:0,max:1,size:1 }));

function selected() { return racers.find(r => r.id === SELECTED_ID); }
function ranks() { return [...racers].sort((a,b)=>b.distance-a.distance); }
function rankOf(r) { return ranks().findIndex(x=>x===r)+1; }

function phaseOf(r) {
  const p = r.distance / RACE_METERS;
  if (p < .08) return "START";
  if (p < .58) return "MID";
  if (p < .82) return "BUILD";
  return "FINAL";
}

function targetSpeed(r) {
  const p = r.distance / RACE_METERS;
  let f = 1;
  if (r.morph === "S") f = p < .28 ? 1.07 : p > .84 ? .985 : 1.015;
  if (r.morph === "P") f = p < .20 ? 1.05 : p > .78 ? .98 : 1.02;
  if (r.morph === "E") f = p < .55 ? .985 : p > .82 ? 1.08 : 1.015;
  if (r.morph === "A") f = p < .18 ? 1.00 : p > .74 ? 1.055 : 1.025;
  return r.cruise * f * (0.79 + 0.21 * r.stamina / 100);
}

function laneFree(r, lane) {
  return racers.every(o => o === r || Math.round(o.laneF) !== lane || Math.abs(o.distance-r.distance) > 8.5);
}

function update(dtMs) {
  const dt = Math.min(45, dtMs) / 1000;
  elapsed += dtMs;
  for (const r of racers) {
    r.cooldown = Math.max(0, r.cooldown - dtMs);
    let target = targetSpeed(r);
    const ahead = racers.filter(o => o !== r && Math.round(o.laneF) === Math.round(r.laneF) && o.distance > r.distance)
      .sort((a,b)=>a.distance-b.distance)[0];
    const gap = ahead ? ahead.distance-r.distance : Infinity;

    if (gap < 10 && r.cooldown <= 0) {
      const candidates = [r.lane-1,r.lane+1].filter(l => l >= 0 && l < LANES && laneFree(r,l));
      if (candidates.length) {
        r.lane = candidates[(r.id + Math.floor(elapsed/1600)) % candidates.length];
        r.cooldown = 900;
        r.command = "SHIFT";
      } else {
        target *= .91;
        r.command = "HOLD";
      }
    } else {
      r.command = phaseOf(r) === "FINAL" ? "COMMIT" : "CRUISE";
    }

    target += Math.sin(elapsed * .0012 + r.seed) * .16;
    const diff = target-r.speed;
    const step = r.accel * dt * (diff >= 0 ? 1 : 1.5);
    r.speed += Math.max(-step, Math.min(step, diff));
    r.distance += Math.max(0,r.speed)*dt;
    r.stamina = Math.max(0, r.stamina - (.22 + Math.max(0,r.speed/r.cruise-.96)*1.8) * r.drain * dt);
    r.laneF += (r.lane-r.laneF) * Math.min(1,dt*4.2);

    if (r.distance >= RACE_METERS) {
      r.distance = RACE_METERS;
      r.speed *= .985;
    }

    if (r.speed > 8 && Math.random() < dt * (r.id === SELECTED_ID ? 11 : 4.5)) spawnDust(r);
  }

  for (const p of particles) {
    if (!p.active) continue;
    p.life -= dtMs;
    if (p.life <= 0) { p.active = false; continue; }
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy -= 1.4 * dt;
    p.size *= 1 + .35 * dt;
  }
}

let dustCursor = 0;
function spawnDust(r) {
  const p = particles[dustCursor++ % particles.length];
  const laneT = r.laneF/(LANES-1);
  const y = trackY(laneT);
  const scale = laneScale(laneT);
  p.active = true;
  p.x = worldX(r.distance) - MORPHS[r.morph].w*scale*.34;
  p.y = y + 5;
  p.vx = -(70 + r.speed*5) * (0.8 + Math.random()*.5);
  p.vy = -4 - Math.random()*8;
  p.life = p.max = 350 + Math.random()*360;
  p.size = 12*scale*(.7+Math.random()*.8);
}

function worldX(distance) {
  const focus = selected();
  const focusX = cameraMode === "chase" ? width * .34 : width * .44;
  const ppm = cameraMode === "chase" ? Math.min(2.2,Math.max(1.25,width/720)) : Math.min(1.6,Math.max(.92,width/950));
  return focusX + (distance-focus.distance)*ppm;
}

function trackY(t) {
  const top = height * .53;
  const bottom = height * .94;
  return top + (bottom-top) * Math.pow(t,1.22);
}

function laneScale(t) {
  return .58 + t*.58;
}

function drawSky(scroll) {
  const g = ctx.createLinearGradient(0,0,0,height*.62);
  g.addColorStop(0,"#5f9fc9");
  g.addColorStop(.48,"#a7c7d6");
  g.addColorStop(1,"#d2c7a5");
  ctx.fillStyle = g;
  ctx.fillRect(0,0,width,height);

  const sx = width*.78, sy=height*.16, sr=Math.max(44,width*.035);
  const glow = ctx.createRadialGradient(sx,sy,0,sx,sy,sr*2.7);
  glow.addColorStop(0,"rgba(255,242,200,.70)");
  glow.addColorStop(1,"rgba(255,242,200,0)");
  ctx.fillStyle=glow;
  ctx.fillRect(sx-sr*2.7,sy-sr*2.7,sr*5.4,sr*5.4);

  mountainLayer(height*.41,88,235,scroll*.10,"#7291a0");
  mountainLayer(height*.47,65,190,scroll*.18,"#597b7a");
  treeLine(height*.49,scroll*.32);
}

function mountainLayer(base,amp,period,shift,color) {
  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.moveTo(0,height);
  ctx.lineTo(0,base);
  for(let x=-period;x<=width+period;x+=period*.5){
    const w=x+shift;
    const peak=base-amp*(.45+.55*Math.abs(Math.sin(w*.0067)));
    ctx.lineTo(x,peak);
    ctx.lineTo(x+period*.22,base-amp*.14);
    ctx.lineTo(x+period*.5,base);
  }
  ctx.lineTo(width,height);
  ctx.closePath();
  ctx.fill();
}

function treeLine(base,shift) {
  ctx.fillStyle="#31513f";
  const gap=58;
  const off=((shift%gap)+gap)%gap;
  for(let x=-gap+off;x<width+gap;x+=gap){
    const h=35+18*Math.abs(Math.sin((x+shift)*.031));
    ctx.beginPath();
    ctx.moveTo(x,base);
    ctx.lineTo(x+10,base-h*.55);
    ctx.lineTo(x+18,base-h*.40);
    ctx.lineTo(x+25,base-h);
    ctx.lineTo(x+35,base-h*.38);
    ctx.lineTo(x+44,base);
    ctx.closePath();
    ctx.fill();
  }
}

function drawGrandstand(scroll) {
  const y=height*.42;
  const speed=scroll*.52;
  const span=360;
  const off=((speed%span)+span)%span;
  for(let x=-span+off;x<width+span;x+=span){
    ctx.fillStyle="rgba(34,48,58,.90)";
    ctx.fillRect(x,y-55,300,57);
    ctx.fillStyle="#d7e0df";
    ctx.fillRect(x-10,y-63,320,7);
    ctx.fillStyle="rgba(194,206,207,.58)";
    for(let r=0;r<5;r++){
      const ry=y-43+r*9;
      for(let c=0;c<26;c++){
        const tone=(c*13+r*7)%3;
        ctx.fillStyle=tone===0?"#b8a58f":tone===1?"#7f939f":"#d1c7b7";
        ctx.fillRect(x+8+c*11,ry,5,4);
      }
    }
    ctx.strokeStyle="rgba(219,232,236,.45)";
    ctx.lineWidth=2;
    ctx.beginPath();
    ctx.moveTo(x,y+1);ctx.lineTo(x+300,y+1);ctx.stroke();
  }
}

function drawTrack(scroll) {
  const top=height*.50, bottom=height;
  const g=ctx.createLinearGradient(0,top,0,bottom);
  g.addColorStop(0,"#b9864e");
  g.addColorStop(.55,"#9d6638");
  g.addColorStop(1,"#744629");
  ctx.fillStyle=g;
  ctx.fillRect(0,top,width,bottom-top);

  for(let lane=0;lane<LANES;lane++){
    const t=lane/(LANES-1);
    const y=trackY(t);
    ctx.strokeStyle=`rgba(255,241,214,${.20+t*.18})`;
    ctx.lineWidth=1+t*1.3;
    ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke();
  }

  const markGap=64;
  const off=((scroll*2.6)%markGap+markGap)%markGap;
  for(let x=-markGap+off;x<width+markGap;x+=markGap){
    const t=(x+120)/(width+240);
    const y=height*(.62+.29*Math.max(0,Math.min(1,t)));
    ctx.fillStyle="rgba(244,223,191,.48)";
    ctx.fillRect(x,y,22+34*t,2+3*t);
  }

  const streakCount = width < 760 ? 55 : 110;
  ctx.strokeStyle="rgba(255,232,196,.20)";
  for(let i=0;i<streakCount;i++){
    const seed=i*97.13;
    const y=top+((Math.sin(seed)*.5+.5)*(bottom-top));
    const x=((seed*31-scroll*4.2)%(width+160)+width+160)%(width+160)-80;
    const len=16+(y-top)/(bottom-top)*46;
    ctx.lineWidth=.7+(y-top)/(bottom-top)*1.8;
    ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x-len,y+1);ctx.stroke();
  }

  ctx.strokeStyle="#e9ece6";
  ctx.lineWidth=4;
  ctx.beginPath();ctx.moveTo(0,top-7);ctx.lineTo(width,top-7);ctx.stroke();
}

function frameIndexFor(r) {
  const ratio=Math.max(.2,Math.min(1.15,r.speed/r.cruise));
  const frameMs=150-(ratio*74);
  return Math.floor((elapsed+r.id*47)/frameMs)%6;
}

function drawRacer(r) {
  const img=sheets.get(r.morph);
  if(!img) return;
  const laneT=r.laneF/(LANES-1);
  const scale=laneScale(laneT)*(cameraMode==="chase"?1.04:.92);
  const x=worldX(r.distance);
  const y=trackY(laneT);
  if(x<-300||x>width+300) return;

  const stat=MORPHS[r.morph];
  const w=stat.w*scale, h=stat.h*scale;
  const frame=frameIndexFor(r);
  const col=frame%3,row=Math.floor(frame/3);
  const sx=col*256, sy=row*256;

  const speedRatio=Math.max(0,Math.min(1.15,r.speed/r.cruise));
  const bob=[0,2,8,15,8,0][frame]*scale*.55;
  const tilt=[0,-.012,-.008,.010,.016,-.005][frame];

  ctx.save();

  const trail = r.id===SELECTED_ID ? 4 : 2;
  for(let t=trail;t>=1;t--){
    ctx.save();
    ctx.globalAlpha=.035*(trail-t+1);
    ctx.translate(x-t*(8+speedRatio*10)*scale,y-h*.5-bob);
    ctx.rotate(tilt);
    ctx.scale(-1,1);
    ctx.drawImage(img,sx,sy,256,256,-w*.5,-h*.5,w,h);
    ctx.restore();
  }

  ctx.fillStyle=`rgba(18,14,12,${.16+.10*scale})`;
  ctx.beginPath();
  ctx.ellipse(x,y+6,w*.34,5+5*scale,0,0,Math.PI*2);
  ctx.fill();

  ctx.translate(x,y-h*.5-bob);
  ctx.rotate(tilt);
  ctx.scale(-1,1);
  ctx.drawImage(img,sx,sy,256,256,-w*.5,-h*.5,w,h);
  ctx.restore();

  if(r.id===SELECTED_ID){
    ctx.strokeStyle="rgba(108,221,255,.78)";
    ctx.lineWidth=1.5;
    ctx.beginPath();
    ctx.arc(x,y-h*.52-bob,Math.max(26,w*.34),0,Math.PI*2);
    ctx.stroke();
  }
}

function drawDust() {
  for(const p of particles){
    if(!p.active) continue;
    const life=Math.max(0,p.life/p.max);
    const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,p.size);
    g.addColorStop(0,`rgba(221,190,145,${.26*life})`);
    g.addColorStop(1,"rgba(221,190,145,0)");
    ctx.fillStyle=g;
    ctx.fillRect(p.x-p.size,p.y-p.size,p.size*2,p.size*2);
  }
}

function drawSpeedFX(speedRatio) {
  const strength=Math.max(0,(speedRatio-.55)/.55);
  if(strength<=0) return;
  ctx.save();
  ctx.strokeStyle=`rgba(214,240,255,${.08*strength})`;
  ctx.lineWidth=1.2;
  const count=width<760?18:34;
  for(let i=0;i<count;i++){
    const y=height*(.16+((i*37)%73)/100*.78);
    const x=((i*191-elapsed*.32)%(width+300)+width+300)%(width+300)-120;
    const len=70+160*strength*((i%5)/5+.25);
    ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x-len,y);ctx.stroke();
  }
  ctx.restore();
}

function render() {
  const s=selected();
  const speedRatio=Math.max(0,Math.min(1.15,s.speed/s.cruise));
  const shake=(cameraMode==="chase"?1.8:1.0)*Math.max(0,speedRatio-.55);
  const scroll=s.distance*44;

  ctx.save();
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.057)*shake*.45);

  drawSky(scroll);
  drawGrandstand(scroll);
  drawTrack(scroll);

  [...racers].sort((a,b)=>a.laneF-b.laneF).forEach(drawRacer);
  drawDust();
  drawSpeedFX(speedRatio);

  const nearRail=height*.965;
  ctx.strokeStyle="rgba(240,244,239,.84)";
  ctx.lineWidth=5;
  ctx.beginPath();ctx.moveTo(0,nearRail);ctx.lineTo(width,nearRail);ctx.stroke();

  const vignette=ctx.createRadialGradient(width*.48,height*.48,height*.18,width*.5,height*.5,width*.76);
  vignette.addColorStop(0,"rgba(0,0,0,0)");
  vignette.addColorStop(1,"rgba(0,0,0,.25)");
  ctx.fillStyle=vignette;ctx.fillRect(-20,-20,width+40,height+40);
  ctx.restore();
}

function fmtTime(ms) {
  const total=ms/1000;
  const min=Math.floor(total/60);
  const sec=Math.floor(total%60);
  const cs=Math.floor((total-Math.floor(total))*100);
  return `${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}

function updateUI(now) {
  const s=selected();
  const order=ranks();
  ui.section.textContent=phaseOf(s);
  ui.clock.textContent=fmtTime(elapsed);
  ui.distance.textContent=`${Math.max(0,Math.round(RACE_METERS-s.distance))} m to go`;
  ui.selectedMorph.textContent=s.morph;
  ui.selectedName.textContent=`#${String(s.id).padStart(2,"0")} ${s.name}`;
  ui.selectedSpeed.textContent=s.speed.toFixed(1);
  ui.selectedRank.textContent=rankOf(s);
  ui.selectedMorph.style.background={S:"#25689e",P:"#9e2b2b",E:"#3d7650",A:"#a16b12"}[s.morph];

  stage.dataset.frameS=String(racers.find(r=>r.morph==="S") ? frameIndexFor(racers.find(r=>r.morph==="S")) : -1);
  stage.dataset.frameP=String(racers.find(r=>r.morph==="P") ? frameIndexFor(racers.find(r=>r.morph==="P")) : -1);
  stage.dataset.frameE=String(racers.find(r=>r.morph==="E") ? frameIndexFor(racers.find(r=>r.morph==="E")) : -1);
  stage.dataset.frameA=String(racers.find(r=>r.morph==="A") ? frameIndexFor(racers.find(r=>r.morph==="A")) : -1);
  stage.dataset.camera=cameraMode;
  stage.dataset.running=s.distance<RACE_METERS?"true":"finished";

  if(now-lastRankPaint>180){
    lastRankPaint=now;
    rankbox.innerHTML=order.slice(0,6).map((r,i)=>{
      const gap=Math.max(0,order[0].distance-r.distance);
      return `<div class="rankrow ${i===0?"lead":""} ${r.id===SELECTED_ID?"selected":""}">
        <span class="pos">${i+1}</span>
        <span class="name"><i class="${r.morph.toLowerCase()}">${r.morph}</i>#${String(r.id).padStart(2,"0")} ${r.name}</span>
        <span class="gap">${i===0?"LEAD":"+"+gap.toFixed(1)+"m"}</span>
      </div>`;
    }).join("");
  }
}

document.querySelectorAll("[data-camera]").forEach(button=>{
  button.addEventListener("click",()=>{
    cameraMode=button.dataset.camera;
    document.querySelectorAll("[data-camera]").forEach(b=>b.classList.toggle("active",b===button));
  });
});

function frame(now) {
  const dt=now-last;
  last=now;
  update(dt);
  render();
  updateUI(now);
  requestAnimationFrame(frame);
}

requestAnimationFrame(now=>{
  last=now;
  frame(now);
});

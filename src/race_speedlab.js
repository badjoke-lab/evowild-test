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
  S: { sheet: "s-run-sheet.svg", cruise: 20.6, accel: 5.4, drain: 1.06, w: 154, h: 128, phase: 0.00 },
  P: { sheet: "p-run-sheet.svg", cruise: 19.8, accel: 6.2, drain: 1.12, w: 162, h: 136, phase: 0.90 },
  E: { sheet: "e-run-sheet.svg", cruise: 19.3, accel: 4.5, drain: 0.82, w: 156, h: 132, phase: 1.80 },
  A: { sheet: "a-run-sheet.svg", cruise: 20.0, accel: 5.3, drain: 0.94, w: 160, h: 126, phase: 2.70 }
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
      distance: Math.max(0, 176 - index * 10.5 + (index % 3) * 2.4),
      speed: m.cruise * (0.86 + ((index * 7) % 5) * 0.018),
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
  const x = worldX(r.distance, r.laneF);
  const y = trackYAt(x, laneT, selected().distance * 58);
  const scale = laneScale(laneT);
  p.active = true;
  p.x = worldX(r.distance, r.laneF) - MORPHS[r.morph].w*scale*.34;
  p.y = y + 5;
  p.vx = -(70 + r.speed*5) * (0.8 + Math.random()*.5);
  p.vy = -4 - Math.random()*8;
  p.life = p.max = 350 + Math.random()*360;
  p.size = 12*scale*(.7+Math.random()*.8);
}

function worldX(distance, laneF = 2.5) {
  const focus = selected();
  const focusX = cameraMode === "chase" ? width * .31 : width * .40;
  const ppm = cameraMode === "chase"
    ? Math.min(5.8, Math.max(3.7, width / 245))
    : Math.min(4.2, Math.max(2.7, width / 340));
  const depthShear = (laneF - (LANES - 1) * 0.5) * (cameraMode === "chase" ? 18 : 13);
  return focusX + (distance - focus.distance) * ppm + depthShear;
}

function trackCurveY(x, scroll) {
  const nx = (x - width * 0.5) / Math.max(1, width);
  const sweep = Math.sin(nx * 2.55 + scroll * 0.010) * height * 0.045;
  const camber = -Math.cos(nx * 1.45 + scroll * 0.006) * height * 0.018;
  return sweep + camber;
}

function trackYAt(x, laneT, scroll) {
  const far = height * 0.505 + trackCurveY(x, scroll);
  const near = height * 0.955 + trackCurveY(x, scroll) * 0.44;
  return far + (near - far) * Math.pow(laneT, 1.18);
}

function laneScale(t) {
  return .68 + t * .33;
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
  const base = height * .455;
  const span = 470;
  const off = ((scroll * .24) % span + span) % span;
  for (let x = -span + off; x < width + span; x += span) {
    ctx.save();
    ctx.translate(x, 0);

    const roof = ctx.createLinearGradient(0, base - 95, 0, base - 50);
    roof.addColorStop(0, "#182630");
    roof.addColorStop(1, "#314450");
    ctx.fillStyle = roof;
    ctx.beginPath();
    ctx.moveTo(-18, base - 92);
    ctx.lineTo(335, base - 92);
    ctx.lineTo(305, base - 58);
    ctx.lineTo(0, base - 58);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = "#d9e0dd";
    ctx.fillRect(-8, base - 100, 350, 7);

    const tiers = [base - 50, base - 39, base - 28, base - 17];
    for (let r = 0; r < tiers.length; r++) {
      const ry = tiers[r];
      ctx.fillStyle = r % 2 ? "#5d6d73" : "#68777b";
      ctx.fillRect(2, ry, 306, 7);
      for (let c = 0; c < 31; c++) {
        const v = (c * 17 + r * 11) % 5;
        ctx.fillStyle = ["#e0c6a1","#98b1b8","#c77b62","#d8d7c9","#8395a0"][v];
        ctx.fillRect(7 + c * 9.6, ry + 1, 4.2, 3.6);
      }
    }

    ctx.strokeStyle = "rgba(222,234,235,.42)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, base - 7);
    ctx.lineTo(308, base - 7);
    ctx.stroke();

    ctx.restore();
  }
}

function drawTrack(scroll) {
  const samples = 44;
  const farPts = [];
  const nearPts = [];
  for (let i = 0; i <= samples; i++) {
    const x = (i / samples) * width;
    farPts.push([x, trackYAt(x, 0, scroll)]);
    nearPts.push([x, trackYAt(x, 1, scroll)]);
  }

  const grad = ctx.createLinearGradient(0, height * .49, 0, height);
  grad.addColorStop(0, "#bd8b55");
  grad.addColorStop(.42, "#9a6339");
  grad.addColorStop(1, "#684028");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(farPts[0][0], farPts[0][1]);
  for (const [x,y] of farPts) ctx.lineTo(x,y);
  for (let i = nearPts.length - 1; i >= 0; i--) ctx.lineTo(nearPts[i][0], nearPts[i][1]);
  ctx.closePath();
  ctx.fill();

  // far apron
  ctx.strokeStyle = "rgba(233,239,231,.95)";
  ctx.lineWidth = 5;
  ctx.beginPath();
  farPts.forEach(([x,y],i)=> i ? ctx.lineTo(x,y-5) : ctx.moveTo(x,y-5));
  ctx.stroke();

  // lane curves
  for (let lane = 1; lane < LANES; lane++) {
    const t = lane / LANES;
    ctx.strokeStyle = `rgba(255,240,211,${.12 + t * .16})`;
    ctx.lineWidth = 1 + t * 1.1;
    ctx.beginPath();
    for (let i = 0; i <= samples; i++) {
      const x = (i / samples) * width;
      const y = trackYAt(x, t, scroll);
      if (i) ctx.lineTo(x,y); else ctx.moveTo(x,y);
    }
    ctx.stroke();
  }

  // moving painted dashes, projected into the curved surface
  const gap = 82;
  const phase = ((scroll * 3.2) % gap + gap) % gap;
  for (let x = -gap + phase; x < width + gap; x += gap) {
    const t = Math.max(0, Math.min(1, (x + 80) / (width + 160)));
    const laneT = .18 + .70 * t;
    const y = trackYAt(x, laneT, scroll);
    const len = 22 + 46 * laneT;
    const slope = (trackCurveY(x + 10, scroll) - trackCurveY(x - 10, scroll)) / 20;
    ctx.save();
    ctx.translate(x,y);
    ctx.rotate(Math.atan(slope));
    ctx.fillStyle = `rgba(250,228,194,${.30 + laneT * .22})`;
    ctx.fillRect(-len * .5, -1.2 - laneT, len, 2.4 + laneT * 2.1);
    ctx.restore();
  }

  // subtle surface streaks
  const streaks = width < 760 ? 48 : 88;
  for (let i = 0; i < streaks; i++) {
    const seed = i * 91.731;
    const x = ((seed * 17 - scroll * 4.8) % (width + 220) + width + 220) % (width + 220) - 110;
    const laneT = ((i * 37) % 100) / 100;
    const y = trackYAt(x, laneT, scroll);
    const len = 15 + laneT * 48;
    ctx.strokeStyle = `rgba(255,235,202,${.035 + laneT * .07})`;
    ctx.lineWidth = .7 + laneT * 1.5;
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x-len,y+1);
    ctx.stroke();
  }

  // near rail with moving posts for strong speed parallax
  const postGap = 78;
  const poff = ((scroll * 5.3) % postGap + postGap) % postGap;
  ctx.strokeStyle = "rgba(239,242,235,.92)";
  ctx.lineWidth = 4;
  ctx.beginPath();
  for (let i = 0; i <= samples; i++) {
    const x = (i / samples) * width;
    const y = trackYAt(x, 1, scroll) - 5;
    if (i) ctx.lineTo(x,y); else ctx.moveTo(x,y);
  }
  ctx.stroke();

  for (let x = -postGap + poff; x < width + postGap; x += postGap) {
    const y = trackYAt(x, 1, scroll);
    ctx.strokeStyle = "rgba(215,225,226,.72)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x,y-5);
    ctx.lineTo(x+3,y+27);
    ctx.stroke();
  }
}

function frameIndexFor(r) {function frameIndexFor(r) {
  const ratio=Math.max(.2,Math.min(1.15,r.speed/r.cruise));
  const frameMs=150-(ratio*74);
  return Math.floor((elapsed+r.id*47)/frameMs)%6;
}

function drawRacer(r) {
  const img=sheets.get(r.morph);
  if(!img) return;
  const laneT=r.laneF/(LANES-1);
  const scale=laneScale(laneT)*(cameraMode==="chase"?1.00:.90);
  const x=worldX(r.distance, r.laneF);
  const scroll=selected().distance*58;
  const y=trackYAt(x,laneT,scroll);
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

  if (speedRatio > .72) {
    const streakAlpha = .06 + (speedRatio - .72) * .12;
    ctx.strokeStyle = `rgba(215,240,251,${Math.max(0,streakAlpha)})`;
    ctx.lineWidth = Math.max(1, 1.6 * scale);
    for (let k = 0; k < 3; k++) {
      const sy2 = y - h * (.30 + k * .16);
      const len = (34 + k * 14) * scale * speedRatio;
      ctx.beginPath();
      ctx.moveTo(x - w * .28, sy2);
      ctx.lineTo(x - w * .28 - len, sy2 + k);
      ctx.stroke();
    }
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
  const scroll=s.distance*58;

  ctx.save();
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.057)*shake*.45);

  drawSky(scroll);
  drawGrandstand(scroll);
  drawTrack(scroll);

  [...racers].sort((a,b)=>a.laneF-b.laneF).forEach(drawRacer);
  drawDust();
  drawSpeedFX(speedRatio);

  // foreground verge / posts: fastest parallax layer
  const vergeY = height * .985;
  ctx.fillStyle = "#223c2c";
  ctx.fillRect(0, vergeY - 10, width, 28);
  const fgGap = 118;
  const fgOff = ((scroll * 7.2) % fgGap + fgGap) % fgGap;
  for (let x = -fgGap + fgOff; x < width + fgGap; x += fgGap) {
    ctx.fillStyle = "rgba(230,237,233,.72)";
    ctx.fillRect(x, vergeY - 28, 4, 34);
  }

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

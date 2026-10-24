// 2.5D Course runtime v1. Prototype values, NOT finalized race rules.
// Structured segments are shared by future Course Builder and race engine.
// All entries deliberately preserve the same 18-runner/Agent simulation.
const segment = (length, surface="firm", width=4, curve=0, grade=0) =>
  ({ length, surface, width, curve, grade });

export const COURSE_PRESETS = Object.freeze([
  {
    id:"ridge-1600", name:"RIDGE 1600", description:"Original 2.5D race baseline",
    weather:"clear", legacyTerrain:true, segments:[
      segment(400), segment(400), segment(400), segment(400)
    ]
  },
  {
    id:"sprint-800", name:"SPRINT 800", description:"Fast, broad straight sections",
    weather:"clear", segments:[
      segment(400,"fast",4,0,0),segment(400,"fast",4,0,0)
    ]
  },
  {
    id:"heavy-1200", name:"HEAVY 1200", description:"Mud, climbs and reduced traction",
    weather:"rain", segments:[
      segment(400,"mud",3,0.12,0.06),
      segment(400,"mud",3,-0.18,-0.04),
      segment(400,"grass",3,0.10,0.015)
    ]
  },
  {
    id:"switchback-1200", name:"SWITCHBACK 1200", description:"Sharp bends and narrow sections",
    weather:"clear", segments:[
      segment(400,"grass",3,0.90,0.025),
      segment(400,"sand",2,-1.0,-0.02),
      segment(400,"firm",3,0.80,0.01)
    ]
  },
  {
    id:"endurance-2400", name:"ENDURANCE 2400", description:"Long mixed-surface endurance test",
    weather:"clear", segments:[
      segment(400,"firm",4,0.05,0.025),
      segment(400,"grass",4,-0.10,0.035),
      segment(400,"firm",4,0.06,-0.025),
      segment(400,"grass",3,0.20,0.035),
      segment(400,"firm",4,-0.12,-0.04),
      segment(400,"firm",4,0.04,-0.02)
    ]
  }
].map(course => Object.freeze({
  ...course,
  distance:course.segments.reduce((sum,part)=>sum+part.length,0),
  segments:Object.freeze(course.segments.map(part=>Object.freeze(part)))
})));

const byId = new Map(COURSE_PRESETS.map(course => [course.id,course]));
export const DEFAULT_COURSE_ID = "ridge-1600";
export function getCourse(id) {
  return byId.get(id) || byId.get(DEFAULT_COURSE_ID);
}

export const SURFACE_SHADES = Object.freeze({
  firm:["#4b5154","#464c4f"],
  fast:["#455c66","#405560"],
  grass:["#516050","#495848"],
  mud:["#514940","#494238"],
  sand:["#6e6251","#655948"]
});

export function courseSectionAt(course, meter) {
  const m=Math.max(0,Math.min(course.distance-0.00001,Number(meter)||0));
  let start=0;
  for (const part of course.segments) {
    if (m<start+part.length) return {part,start,end:start+part.length,progress:(m-start)/part.length};
    start+=part.length;
  }
  const part=course.segments[course.segments.length-1];
  return {part,start:start-part.length,end:start,progress:1};
}

// Coefficients are transparent and provisional; no scripted winners.
// Pressure is measured by the existing proximity resolver, not fabricated here.
export function courseEffects(course, meter, morph, pressure=0) {
  const {part}=courseSectionAt(course,meter);
  const base = {
    firm:{S:1,P:1,E:1,A:1},
    fast:{S:1.055,P:1.005,E:1.01,A:1.015},
    grass:{S:.965,P:.99,E:1.005,A:1.015},
    mud:{S:.88,P:1.015,E:.955,A:.97},
    sand:{S:.91,P:.98,E:.965,A:.985}
  }[part.surface] || {S:1,P:1,E:1,A:1};
  const curvePenalty=Math.abs(part.curve)*({S:.10,P:.11,E:.075,A:.025}[morph] ?? .10);
  const uphill=Math.max(0,part.grade);
  const downhill=Math.max(0,-part.grade);
  const hillPenalty=uphill*({S:.80,P:.25,E:.40,A:.48}[morph] ?? .65);
  const downhillGain=downhill*0.20;
  const narrowPressure=Math.max(0,4-part.width)*Math.max(0,Math.min(1,pressure))*0.04;
  const rainPenalty=course.weather==="rain" ? .012 : 0;
  const pace=Math.max(.60,base[morph] * (1-curvePenalty-hillPenalty+downhillGain-narrowPressure-rainPenalty));
  const drainSurface={firm:1,fast:1.035,grass:1.035,mud:1.13,sand:1.11}[part.surface] ?? 1;
  const drainAptitude={
    S:{fast:1.025,mud:1.10,sand:1.07},
    P:{mud:.90,sand:.95},
    E:{fast:.96,grass:.94,firm:.97},
    A:{grass:.96,sand:.96}
  }[morph] || {};
  const stamina=drainSurface*(drainAptitude[part.surface]||1)*(1+uphill*1.2);
  return {pace,stamina,surface:part.surface,width:part.width,curve:part.curve,grade:part.grade};
}

// Draft validation contract for the future player Course Builder.
// Invalid data is never silently clipped or treated as valid race geometry.
export function validateCourse(draft) {
  const errors=[];
  if (!draft || typeof draft!=="object") return {valid:false,errors:["course object required"]};
  if (!Array.isArray(draft.segments) || draft.segments.length<1 || draft.segments.length>20) {
    return {valid:false,errors:["segments must contain 1..20 modules"]};
  }
  let total=0;
  for (const [index,part] of draft.segments.entries()) {
    if (!Number.isInteger(part.length) || part.length<100 || part.length>800) errors.push(`segment ${index}: length must be 100..800m`);
    if (!SURFACE_SHADES[part.surface]) errors.push(`segment ${index}: surface is unknown`);
    if (!Number.isInteger(part.width) || part.width<2 || part.width>4) errors.push(`segment ${index}: width must be 2..4`);
    if (typeof part.curve!=="number" || !Number.isFinite(part.curve) || Math.abs(part.curve)>1) errors.push(`segment ${index}: curve out of range`);
    if (typeof part.grade!=="number" || !Number.isFinite(part.grade) || Math.abs(part.grade)>.12) errors.push(`segment ${index}: grade out of range`);
    total+=part.length;
  }
  if (total<800 || total>4000 || !Number.isFinite(total)) errors.push("total length must be 800..4000m");
  return {valid:errors.length===0,errors,distance:total};
}

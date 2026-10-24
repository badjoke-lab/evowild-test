// EvoWild Run: deterministic, service-independent Race Agent prototype.
// All 18 entrants use exactly this schema; a player-edited Agent File is not
// a privileged control channel. This is provisional logic, not final balance.
export const AGENT_SCHEMA_VERSION = 1;
const CHOICES = Object.freeze({
  start:["PUSH","STANDARD","HOLD"],
  basePace:["CONSERVE","STANDARD","AGGRESSIVE"],
  positioning:["INSIDE","NATURAL","OUTSIDE"],
  traffic:["WAIT","FIND_GAP","OVERTAKE"],
  stamina:["CONSERVE","BALANCED","WIN"],
  spurt:["EARLY","STANDARD","LATE"],
  tired:["SLOW","MAINTAIN","PUSH"]
});
export const AGENT_FIELDS = Object.freeze([
  {key:"start",label:"スタート",choices:CHOICES.start},
  {key:"basePace",label:"基本ペース",choices:CHOICES.basePace},
  {key:"positioning",label:"位置取り",choices:CHOICES.positioning},
  {key:"traffic",label:"混雑時",choices:CHOICES.traffic},
  {key:"stamina",label:"スタミナ運用",choices:CHOICES.stamina},
  {key:"spurt",label:"スパート",choices:CHOICES.spurt},
  {key:"tired",label:"疲労時",choices:CHOICES.tired}
]);
export const AGENT_PRESETS = Object.freeze({
  FRONT:{start:"PUSH",basePace:"AGGRESSIVE",positioning:"INSIDE",traffic:"FIND_GAP",stamina:"WIN",spurt:"EARLY",tired:"MAINTAIN"},
  STALKER:{start:"STANDARD",basePace:"STANDARD",positioning:"INSIDE",traffic:"FIND_GAP",stamina:"BALANCED",spurt:"STANDARD",tired:"MAINTAIN"},
  BALANCED:{start:"STANDARD",basePace:"STANDARD",positioning:"NATURAL",traffic:"FIND_GAP",stamina:"BALANCED",spurt:"STANDARD",tired:"MAINTAIN"},
  CLOSER:{start:"HOLD",basePace:"CONSERVE",positioning:"OUTSIDE",traffic:"FIND_GAP",stamina:"CONSERVE",spurt:"LATE",tired:"MAINTAIN"},
  DEEP_CLOSER:{start:"HOLD",basePace:"CONSERVE",positioning:"OUTSIDE",traffic:"OVERTAKE",stamina:"CONSERVE",spurt:"LATE",tired:"PUSH"}
});
export function makeAgentFile(preset="BALANCED") {
  return {
    agent_version:AGENT_SCHEMA_VERSION,
    ...AGENT_PRESETS[preset] ?? AGENT_PRESETS.BALANCED
  };
}
export function validateAgentFile(value){
  const errors=[];
  if (!value || typeof value!=="object" || Array.isArray(value)) return {valid:false,errors:["Agent File must be an object"]};
  if(value.agent_version!==AGENT_SCHEMA_VERSION)errors.push("Unsupported agent_version");
  const keys=Object.keys(value);
  for(const key of keys){
    if(key!=="agent_version" && !Object.hasOwn(CHOICES,key))errors.push("Unknown field: "+key);
  }
  for(const [key,allowed] of Object.entries(CHOICES)){
    if(!allowed.includes(value[key]))errors.push("Invalid "+key);
  }
  return {valid:errors.length===0,errors};
}
export function normalizedAgentFile(value) {
  const verdict=validateAgentFile(value);
  if(!verdict.valid) return {file:null,errors:verdict.errors};
  const file={agent_version:AGENT_SCHEMA_VERSION};
  for(const field of AGENT_FIELDS)file[field.key]=value[field.key];
  return {file,errors:[]};
}
// Commands are proposals, not guaranteed movements. Existing Creature response
// resolver determines speed and stamina effects; lane safety remains mandatory.
export function decideAgentAction(file,{progress,pressure,stamina,fatigue,blocked}){
  const p=Math.max(0,Math.min(1,progress));
  if(fatigue>=.68 || stamina<=27) {
    if(file.tired==="PUSH" && stamina>13)return {command:"PUSH",reason:"Fatigued final effort"};
    if(file.tired==="SLOW")return {command:"CONSERVE",reason:"High fatigue"};
    return {command:"HOLD",reason:"Fatigued: maintain line"};
  }
  if(pressure>=.35 && blocked) {
    if(file.traffic!=="WAIT")return {command:"SHIFT_LINE",reason:"Congestion: find safe opening"};
    return {command:"HOLD",reason:"Hold line in traffic"};
  }
  const threshold={EARLY:.64,STANDARD:.78,LATE:.89}[file.spurt];
  const reserve=file.stamina==="CONSERVE" ? 49 : file.stamina==="BALANCED" ? 35 : 24;
  if(p>=threshold && stamina>=reserve)return {command:"PUSH",reason:"Autonomous final spurt"};
  if(p<.10){
    if(file.start==="PUSH")return {command:"PUSH",reason:"Start strategy"};
    if(file.start==="HOLD")return {command:"CONSERVE",reason:"Restrained start"};
    return {command:"HOLD",reason:"Standard start"};
  }
  if(file.basePace==="AGGRESSIVE" && stamina>52 && p<.86 && file.stamina!=="CONSERVE")
    return {command:"PUSH",reason:"Aggressive base pace"};
  if(file.basePace==="CONSERVE" || (file.stamina==="CONSERVE" && p<.7))
    return {command:"CONSERVE",reason:"Conserve for later phase"};
  return {command:"HOLD",reason:"Hold planned pace"};
}

import {validateAgentFile} from "./race_agent_v1.js";
// EvoWild Run — local-only playable loop storage v1.
// This is a prototype. No account, server authority, real ownership or online race record.
export const GAME_STORAGE_KEY="evowild:2p5d:game:v1";
export const RACE_COURSE_ID="oval-1600-prototype";
export const ENTRANTS=Object.freeze([
  {id:1,name:"Mica",morph:"S"},{id:2,name:"Vela",morph:"P"},
  {id:3,name:"Rook",morph:"E"},{id:4,name:"Serein",morph:"A"},
  {id:5,name:"Flint",morph:"S"},{id:6,name:"Nacre",morph:"P"},
  {id:7,name:"Ilex",morph:"E"},{id:8,name:"Sora",morph:"A"},
  {id:9,name:"Tarin",morph:"S"},{id:10,name:"Ossa",morph:"P"},
  {id:11,name:"Brink",morph:"E"},{id:12,name:"Nyx",morph:"A"},
  {id:13,name:"Arden",morph:"S"},{id:14,name:"Vale",morph:"P"},
  {id:15,name:"Kest",morph:"E"},{id:16,name:"Orin",morph:"A"},
  {id:17,name:"Tess",morph:"S"},{id:18,name:"Moro",morph:"P"}
].map(r=>Object.freeze(r)));

export const defaultGameState=()=>({
  schemaVersion:1,selectedRunnerId:1,
  history:[]
});

const isId=x=>Number.isInteger(x)&&x>=1&&x<=18;
const isFiniteTime=x=>Number.isFinite(x)&&x>0&&x<1_000_000;
const isValidEntry=e=>e&&isId(e.id)&&typeof e.name==="string"&&
 e.name.length<=48&&["S","P","E","A"].includes(e.morph)&&
 Number.isInteger(e.place)&&e.place>=1&&e.place<=18&&isFiniteTime(e.timeMs);
export function validateRaceRecord(record){
  if(!record||typeof record!=="object")return false;
  if(record.schemaVersion!==1||record.courseId!==RACE_COURSE_ID)return false;
  if(typeof record.id!=="string"||record.id.length<8||record.id.length>100)return false;
  if(!Number.isFinite(record.finishedAt)||record.finishedAt<=0)return false;
  if(!isId(record.playerRunnerId)||!Array.isArray(record.results)||record.results.length!==18)return false;
  if(record.agentFile !== undefined && !validateAgentFile(record.agentFile).valid)return false;
  if(record.agentDecisions !== undefined){
    if(!Array.isArray(record.agentDecisions)||record.agentDecisions.length>30)return false;
    if(record.agentDecisions.some(d=> !d||!Number.isFinite(d.at)||d.at<0||
       !["PUSH","CONSERVE","HOLD","SHIFT_LINE"].includes(d.command)||
       !["SUCCESS","PARTIAL","FAILED","PENDING"].includes(d.result)||
       typeof d.reason!=="string"||d.reason.length>160))return false;
  }
  if(record.results.some(e=>!isValidEntry(e)))return false;
  const ids=new Set(record.results.map(e=>e.id));
  const places=new Set(record.results.map(e=>e.place));
  if(ids.size!==18||places.size!==18)return false;
  for(let i=1;i<=18;i++)if(!places.has(i)||!ids.has(i))return false;
  const player=record.results.find(e=>e.id===record.playerRunnerId);
  return Boolean(player)&&player.place===record.playerPlace;
}
export function validateGameState(value){
  return Boolean(value&&value.schemaVersion===1&&isId(value.selectedRunnerId)&&
    Array.isArray(value.history)&&value.history.length<=50&&
    value.history.every(validateRaceRecord)&&
    new Set(value.history.map(e=>e.id)).size===value.history.length);
}
export function loadGameState(storage){
  try{
    const raw=storage?.getItem(GAME_STORAGE_KEY);
    if(!raw)return defaultGameState();
    const state=JSON.parse(raw);
    return validateGameState(state)?state:defaultGameState();
  }catch{return defaultGameState();}
}
export function storeGameState(storage,state){
  if(!validateGameState(state))return false;
  try{storage.setItem(GAME_STORAGE_KEY,JSON.stringify(state));return true;}
  catch{return false;}
}
export function selectPlayerRunner(storage,id){
  if(!isId(id))return false;
  const state=loadGameState(storage);
  state.selectedRunnerId=id;
  return storeGameState(storage,state);
}
export function makeRaceRecord({id,finishedAt,selectedRunnerId,results,agentFile,agentDecisions}){
  const entries=Array.isArray(results)?results.map(r=>({
    id:Number(r.id),name:String(r.name),morph:String(r.morph),
    place:Number(r.finishPlace),timeMs:Number(r.finishTime)
  })):null;
  const player=entries?.find(r=>r.id===selectedRunnerId);
  const record={
    schemaVersion:1,id,finishedAt,courseId:RACE_COURSE_ID,
    playerRunnerId:selectedRunnerId,playerPlace:player?.place,
    results:entries,
    ...(agentFile ? {agentFile} : {}),
    ...(agentDecisions ? {agentDecisions:agentDecisions.map(d=>({
      at:Number(d.at),command:String(d.command),
      result:String(d.result),reason:String(d.reason)
    }))} : {})
  };
  return validateRaceRecord(record)?record:null;
}
export function appendRaceResult(storage,record){
  if(!validateRaceRecord(record))return false;
  const state=loadGameState(storage);
  if(state.history.some(r=>r.id===record.id))return true;
  const next={...state,selectedRunnerId:record.playerRunnerId,
    history:[record,...state.history].slice(0,50)};
  return storeGameState(storage,next);
}
export function formatRaceTime(ms){
  const cs=Math.max(0,Math.floor(ms/10));
  return String(Math.floor(cs/6000)).padStart(2,"0")+":"+
    String(Math.floor(cs/100)%60).padStart(2,"0")+"."+
    String(cs%100).padStart(2,"0");
}

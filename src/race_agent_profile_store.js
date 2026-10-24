import { makeAgentFile, normalizedAgentFile, AGENT_PRESETS } from "./race_agent_v1.js";
export const agentProfileKey=id=>"evowild:2p5d:agent:"+id+":v1";
const validRunnerId=id=>Number.isInteger(id)&&id>=1&&id<=18;
export function loadAgentProfile(storage,runnerId){
  if(!validRunnerId(runnerId))return makeAgentFile();
  try{
    const json=storage.getItem(agentProfileKey(runnerId));
    if(!json)return makeAgentFile();
    return normalizedAgentFile(JSON.parse(json)).file ?? makeAgentFile();
  }catch{return makeAgentFile();}
}
export function saveAgentProfile(storage,runnerId,input){
  if(!validRunnerId(runnerId))return false;
  const {file}=normalizedAgentFile(input);
  if(!file)return false;
  try{storage.setItem(agentProfileKey(runnerId),JSON.stringify(file));return true;}
  catch{return false;}
}
export function matchedAgentPreset(file){
  for(const [key,fields] of Object.entries(AGENT_PRESETS)){
    if(Object.entries(fields).every(([field,value])=>file?.[field]===value))return key;
  }
  return "CUSTOM";
}

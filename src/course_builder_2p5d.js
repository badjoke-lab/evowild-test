import {
  COURSE_PRESETS, PLAYER_COURSE_KEY,
  buildPlayerCourse, validateCourse, SURFACE_SHADES
} from "./course_profiles_2p5d.js";

const $=selector=>document.querySelector(selector);
const defaultDraft=()=>({
  version:1,name:"My First Course",weather:"clear",
  segments:COURSE_PRESETS[0].segments.map(part=>({...part}))
});
let draft=defaultDraft();
try {
  const saved=JSON.parse(localStorage.getItem(PLAYER_COURSE_KEY) || "null");
  if (buildPlayerCourse(saved).course) draft=saved;
} catch { /* invalid local draft is never promoted */ }
$("#courseName").value=draft.name;
$("#weather").value=draft.weather;

function change() {
  draft.name=$("#courseName").value;
  draft.weather=$("#weather").value;
  $("#saveState").textContent="Unsaved changes";
  render();
}
$("#courseName").addEventListener("input",change);
$("#weather").addEventListener("change",change);

function drawTrace(){
  const svg=$("#courseTrace");
  svg.replaceChildren();
  const el=(tag,attrs)=> {
    const node=document.createElementNS("http://www.w3.org/2000/svg",tag);
    for (const [key,val] of Object.entries(attrs)) node.setAttribute(key,String(val));
    svg.append(node);
    return node;
  };
  const total=draft.segments.reduce((sum,part)=>sum+part.length,0)||1;
  let x=20,elevation=120,heading=0,pointlist=[[x,elevation]];
  el("path",{d:"M20 120 L460 120",stroke:"#34464e","stroke-dasharray":"6 6","stroke-width":1,fill:"none"});
  for(const part of draft.segments){
    const nextX=x+part.length/total*440;
    const nextY=elevation-part.grade*part.length*.40;
    const middleX=(x+nextX)/2;
    const middleY=(elevation+nextY)/2 + part.curve*26;
    const path="M "+x.toFixed(2)+" "+elevation.toFixed(2)+
      " Q "+middleX.toFixed(2)+" "+middleY.toFixed(2)+
      " "+nextX.toFixed(2)+" "+nextY.toFixed(2);
    const color={
      firm:"#a5b1b2",fast:"#80b6db",grass:"#a7d595",mud:"#b39a79",sand:"#d4c18a"
    }[part.surface]||"#eee";
    el("path",{d:path,stroke:"#121d26","stroke-width":part.width*4+6,fill:"none","stroke-linecap":"round"});
    el("path",{d:path,stroke:color,"stroke-width":part.width*3,fill:"none","stroke-linecap":"round"});
    el("path",{d:path,stroke:"#e6f4f5","stroke-width":1.2,fill:"none","stroke-dasharray":"3 7"});
    x=nextX;elevation=nextY;heading+=part.curve;
    pointlist.push([x,elevation]);
  }
  el("circle",{cx:20,cy:120,r:5,fill:"#9affd5"});
  el("circle",{cx:x,cy:elevation,r:6,fill:"#ffcc77"});
}
function render(){
  const container=$("#segments");
  container.replaceChildren();
  draft.segments.forEach((part,index)=>{
    const div=document.createElement("div");
    div.className="segment";
    const line=document.createElement("div");line.className="segment-main";
    const badge=document.createElement("strong");badge.textContent=String(index+1).padStart(2,"0");
    const info=document.createElement("span");info.textContent=
      part.length+"m · "+part.surface.toUpperCase()+" · "+part.width+" LANES · "+
      (part.curve>0?"LEFT ":part.curve<0?"RIGHT ":"STRAIGHT ")+
      Math.round(Math.abs(part.curve)*100)+" · "+
      (part.grade===0?"FLAT":(part.grade>0?"UP ":"DOWN ")+Math.round(Math.abs(part.grade)*100)+"%");
    line.append(badge,info);
    const actions=document.createElement("div");actions.className="segment-buttons";
    const action=(label,disabled,callback)=>{
      const button=document.createElement("button");
      button.textContent=label;button.type="button";button.disabled=disabled;
      button.addEventListener("click",()=>{callback();$("#saveState").textContent="Unsaved changes";render();});
      actions.append(button);
    };
    action("↑",index===0,()=>{[draft.segments[index-1],draft.segments[index]]=[draft.segments[index],draft.segments[index-1]];});
    action("↓",index===draft.segments.length-1,()=>{[draft.segments[index+1],draft.segments[index]]=[draft.segments[index],draft.segments[index+1]];});
    action("×",draft.segments.length===1,()=>draft.segments.splice(index,1));
    div.append(line,actions);container.append(div);
  });
  const {course,errors}=buildPlayerCourse(draft);
  const total=draft.segments.reduce((sum,part)=>sum+part.length,0);
  $("#distance").textContent=total.toLocaleString();
  $("#sections").textContent=String(draft.segments.length);
  $("#surfaceTypes").textContent=String(new Set(draft.segments.map(part=>part.surface)).size);
  $("#segmentCount").textContent=draft.segments.length+" modules";
  $("#validation").textContent=course?
    "READY TO TEST · Valid local Course draft" :
    "FIX BEFORE TEST: "+errors.join("; ");
  $("#validation").dataset.valid=course?"1":"0";
  for(const selector of ["#saveCourse","#testCourse","#exportCourse"]) $(selector).disabled=!course;
  drawTrace();
}

$("#addSegment").addEventListener("submit",event=>{
  event.preventDefault();
  const data=new FormData(event.currentTarget);
  const part={
    length:Number(data.get("length")),surface:String(data.get("surface")),
    width:Number(data.get("width")),curve:Number(data.get("curve")),grade:Number(data.get("grade"))
  };
  draft.segments.push(part);
  $("#saveState").textContent="Unsaved changes";
  render();
});
function save(){
  const result=buildPlayerCourse(draft);
  if (!result.course)return false;
  try{
    localStorage.setItem(PLAYER_COURSE_KEY,JSON.stringify({
      version:1,name:result.course.name,weather:result.course.weather,
      segments:result.course.segments
    }));
    $("#saveState").textContent="Saved locally";
    return true;
  }catch(err){
    $("#validation").textContent="Cannot save: local storage is unavailable";
    return false;
  }
}
$("#saveCourse").addEventListener("click",save);
$("#testCourse").addEventListener("click",()=>{
  if(!save())return;
  const url=new URL("./race-quality.html",window.location.href);
  url.searchParams.set("course","custom");
  window.location.assign(url.toString());
});
$("#exportCourse").addEventListener("click",()=>{
  const result=buildPlayerCourse(draft);
  if (!result.course)return;
  const blob=new Blob([JSON.stringify({version:1,name:result.course.name,weather:result.course.weather,segments:result.course.segments},null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");a.href=url;a.download="evowild-course.json";a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$("#importCourse").addEventListener("change",async event=>{
  const file=event.target.files?.[0];if(!file)return;
  try{
    const imported=JSON.parse(await file.text());
    const normalized=buildPlayerCourse(imported);
    if(!normalized.course)throw Error(normalized.errors.join("; "));
    draft={version:1,name:normalized.course.name,weather:normalized.course.weather,segments:normalized.course.segments.map(part=>({...part}))};
    $("#courseName").value=draft.name;
    $("#weather").value=draft.weather;
    $("#saveState").textContent="Imported / unsaved";
    render();
  } catch(err) {
    $("#validation").textContent="IMPORT ERROR: "+String(err?.message||err);
    $("#validation").dataset.valid="0";
  }
  event.target.value="";
});
render();

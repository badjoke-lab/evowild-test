import {
  ENTRANTS, loadGameState, selectPlayerRunner, GAME_STORAGE_KEY,formatRaceTime
} from "./game_progress_2p5d.js";

const $=selector=>document.querySelector(selector);
const MORPH_TEXT={S:"スプリント型",P:"パワー型",E:"持久型",A:"アジリティ型"};
const concept=(morph)=>import.meta.env.BASE_URL+"concept/"+morph+".webp";
const state=loadGameState(localStorage);
let chosenId=state.selectedRunnerId;
const chosen=()=>ENTRANTS.find(r=>r.id===chosenId) || ENTRANTS[0];
const el=(tag,cls,text)=>{
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(text!=null)node.textContent=String(text);
  return node;
};
const raceUrl=()=> {
  const url=new URL("./race-stadium.html",location.href);
  url.searchParams.set("selected",String(chosenId));
  return url.href;
};
function updateRaceLinks(){
  for(const node of document.querySelectorAll('a[id^="playFrom"]')){
    node.href=raceUrl();
  }
}
function updateSelected(){
  const person=chosen();
  $("#heroCreatureArt").src=concept(person.morph);
  $("#heroCreatureName").textContent="#"+String(person.id).padStart(2,"0")+" "+person.name;
  $("#heroCreatureMorph").textContent=person.morph+" · "+MORPH_TEXT[person.morph];
  $("#selectionArt").src=concept(person.morph);
  $("#selectionName").textContent="#"+String(person.id).padStart(2,"0")+" "+person.name;
  $("#selectionMorph").textContent=person.morph+" · "+MORPH_TEXT[person.morph];
  for(const c of $("#creatureGrid").children){
    const active=Number(c.dataset.runnerId)===person.id;
    c.dataset.selected=active?"true":"false";
    c.setAttribute("aria-pressed",active?"true":"false");
  }
  updateRaceLinks();
}
function buildEntrants(){
  const grid=$("#creatureGrid");
  grid.replaceChildren(...ENTRANTS.map(r=>{
    const card=el("button","creature-card");
    card.type="button";card.dataset.runnerId=String(r.id);
    const img=el("img","creature-icon");
    img.src=concept(r.morph);img.alt="";
    const names=el("span","creature-titles");
    names.append(el("strong","",r.name),el("small","",r.morph+" / "+MORPH_TEXT[r.morph]));
    const number=el("span","creature-number","#"+String(r.id).padStart(2,"0"));
    card.append(img,names,number);
    card.addEventListener("click",()=>{
      chosenId=r.id;
      $("#saveNotice").textContent="選択中。保存するには「この個体を選択」を押してください。";
      updateSelected();
    });
    return card;
  }));
}
$("#saveCreature").addEventListener("click",()=>{
  const ok=selectPlayerRunner(localStorage,chosenId);
  $("#saveNotice").textContent=ok
    ? "選択をこのブラウザに保存しました。"
    : "ブラウザへの保存に失敗しました。出走はこのまま可能です。";
});
function displayHistory(){
  const data=loadGameState(localStorage);
  $("#homeHistoryCount").textContent="記録 "+data.history.length+" レース";
  const host=$("#historyList");
  host.replaceChildren();
  $("#historyEmpty").hidden=data.history.length>0;
  for(const record of data.history){
    const card=el("article","history-card");
    const header=el("div","history-head");
    const date=el("time","",new Date(record.finishedAt).toLocaleString("ja-JP"));
    const summary=el("strong","",record.playerPlace+" / 18 着");
    header.append(date,summary);
    const player=record.results.find(r=>r.id===record.playerRunnerId);
    card.append(header,el("h2","", "#"+String(player.id).padStart(2,"0")+" "+player.name+" · "+player.morph+"型"),
      el("p","history-meta","オーバル1600 · "+formatRaceTime(player.timeMs)));
    const disclosure=el("details","history-details");
    disclosure.append(el("summary","","全18体の着順を見る"));
    const table=el("ol","race-places");
    for(const entry of [...record.results].sort((a,b)=>a.place-b.place)){
      const row=el("li",entry.id===record.playerRunnerId?"mine":"");
      row.append(el("span","",entry.place+"着  "+entry.morph+String(entry.id).padStart(2,"0")+" "+entry.name),
        el("time","",formatRaceTime(entry.timeMs)));
      table.append(row);
    }
    disclosure.append(table);
    card.append(disclosure);
    if(record.agentDecisions?.length){
      const agentLog=el("details","agent-history-details");
      agentLog.append(el("summary","","Race Agent 判断ログ ("+record.agentDecisions.length+"件)"));
      const list=el("ol","agent-history-list");
      for(const action of [...record.agentDecisions].reverse()){
        const row=el("li","");
        row.append(
          el("time","",formatRaceTime(action.at)),
          el("strong","",action.command.replace("_"," ")),
          el("span","",action.result),
          el("small","",action.reason)
        );
        list.append(row);
      }
      agentLog.append(list);
      card.append(agentLog);
    }
    host.append(card);
  }
}
$("#exportHistory").addEventListener("click",()=>{
  const data=loadGameState(localStorage);
  const blob=new Blob([JSON.stringify({schemaVersion:1,history:data.history},null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);
  const link=document.createElement("a");link.href=url;link.download="evowild-2p5d-race-history.json";link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
function activateNav(){
  const current=["home","course","creatures","history"].includes(location.hash.slice(1))
    ? location.hash.slice(1):"home";
  for(const view of document.querySelectorAll(".view"))view.hidden=view.id!==current;
  for(const a of document.querySelectorAll("[data-nav]")) {
    a.dataset.active=a.dataset.nav===current?"true":"false";
    if(a.dataset.nav===current)a.setAttribute("aria-current","page");
    else a.removeAttribute("aria-current");
  }
  if(current==="history")displayHistory();
}
buildEntrants();
updateSelected();
displayHistory();
activateNav();
window.addEventListener("hashchange",activateNav);
window.addEventListener("pageshow",()=>{
  displayHistory();
  updateRaceLinks();
});

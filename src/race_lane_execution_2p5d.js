// Provenance and observed execution only; lane selection/physics stay in the engine.
export function recordLaneExecution(runner,{source,at,targetLane,reason,decision}) {
  const event=decision ?? {at,command:"SHIFT_LINE",reason,result:"PENDING"};
  Object.assign(event,{source,fromLane:runner.lane,targetLane,actualLane:runner.lane,observedAt:at});
  if(source==="ENGINE") {
    runner.engineLaneChanges ??= [];
    runner.engineLaneChanges.unshift(event);
    runner.engineLaneChanges.length=Math.min(30,runner.engineLaneChanges.length);
  }
  // A rejected Agent request must not take ownership of an existing movement.
  if(event.result==="PENDING"){
    const previous=runner.activeLaneExecution;
    runner.activeLaneExecution=event;
    // Freeze the previous decision at takeover, before the new owner moves.
    if(previous && previous!==event)observeLaneExecution(previous,runner,at);
  }
  return event;
}

export function observeLaneExecution(event,runner,elapsed,expiresAt=Infinity) {
  if(!event || event.result!=="PENDING")return event?.result;
  event.actualLane=runner.lane;
  event.observedAt=elapsed;
  const remaining=Math.abs(runner.lane-event.targetLane);
  const interrupted=(runner.activeLaneExecution && runner.activeLaneExecution!==event) ||
    runner.targetLane!==event.targetLane;
  // Arrival under another decision's ownership cannot credit this request.
  if(!interrupted && remaining<1e-6)event.result="SUCCESS";
  else if(interrupted || runner.finished || elapsed>=expiresAt) {
    const initial=Math.abs(event.fromLane-event.targetLane);
    event.result=remaining<initial-1e-6 ? "PARTIAL" : "FAILED";
  }
  return event.result;
}

// Display human lane numbers (1–4); fractions show actual movement between lanes.
export function laneExecutionText(event) {
  if(event.fromLane===undefined)return ""; // Historical v1 records lack lane observations.
  const lane=value=>value===null?"なし":(value+1).toFixed(2);
  return `開始 ${lane(event.fromLane)} → 目標 ${lane(event.targetLane)} / 観測 ${lane(event.actualLane)} (${(event.observedAt/1000).toFixed(2)}s)`;
}
export const laneSourceLabel=source=>source==="ENGINE"?"エンジン進路調整":"Agent 指令";

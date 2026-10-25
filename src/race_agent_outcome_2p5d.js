// Record observed execution, not the acceptance of a target-lane request.
// This uses the existing prototype result vocabulary; it adds no random grade.
export function resolveRecordedAgentDecision(runner, elapsed) {
  const agent=runner.agent;
  const decision=agent?.decisions?.[0];
  if(!decision || decision.result!=="PENDING")return decision?.result;
  if(decision.command==="SHIFT_LINE") {
    const remaining=Math.abs(runner.lane-decision.targetLane);
    if(remaining<1e-6)decision.result="SUCCESS";
    else if(runner.finished || elapsed>=agent.commandUntil || runner.targetLane!==decision.targetLane) {
      const initial=Math.abs(decision.fromLane-decision.targetLane);
      decision.result=remaining<initial-1e-6 ? "PARTIAL" : "FAILED";
    }
    agent.lastResult=decision.result;
  } else {
    const grade={STRONG:"SUCCESS",SETTLED:"SUCCESS",PARTIAL:"PARTIAL",WEAK:"FAILED",EXPIRED:"FAILED"};
    if(grade[agent.lastResult])decision.result=grade[agent.lastResult];
  }
  return decision.result;
}

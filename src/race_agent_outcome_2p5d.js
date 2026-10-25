import {observeLaneExecution} from "./race_lane_execution_2p5d.js";
// Record observed execution, not the acceptance of a target-lane request.
// This uses the existing prototype result vocabulary; it adds no random grade.
export function resolveRecordedAgentDecision(runner, elapsed) {
  const agent=runner.agent;
  const decision=agent?.decisions?.[0];
  if(!decision || decision.result!=="PENDING")return decision?.result;
  if(decision.command==="SHIFT_LINE") {
    observeLaneExecution(decision,runner,elapsed,agent.commandUntil);
    agent.lastResult=decision.result;
  } else {
    const grade={STRONG:"SUCCESS",SETTLED:"SUCCESS",PARTIAL:"PARTIAL",WEAK:"FAILED",EXPIRED:"FAILED"};
    if(grade[agent.lastResult])decision.result=grade[agent.lastResult];
  }
  return decision.result;
}

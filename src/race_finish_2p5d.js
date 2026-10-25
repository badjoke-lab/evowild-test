// Resolve crossings within one fixed simulation step. A runner's array position
// must not decide a photo finish. Keep the engine's piecewise-linear movement;
// interpolate only the time at which that movement reaches the finish line.
export function classifyFinishCrossings(crossings, {stepEndMs, stepMs, finishCount, finishDistance}) {
  const timed = crossings.map(({runner, fromDistance, toDistance}) => ({
    runner,
    time: stepEndMs - stepMs + stepMs * Math.max(0, Math.min(1,
      (finishDistance - fromDistance) / (toDistance - fromDistance)
    ))
  })).sort((a, b) => a.time - b.time);
  for (const {runner, time} of timed) {
    runner.finishPlace = ++finishCount;
    runner.finishTime = time;
  }
  return finishCount;
}

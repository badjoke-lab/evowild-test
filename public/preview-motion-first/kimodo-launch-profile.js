// Generated from the real NVIDIA Kimodo sprint-v1 source clip.
// Only the normalized launch-establishment envelope is used. Absolute human
// speed/cadence/stance/joint values are intentionally excluded.
export const KIMODO_SPRINT_SOURCE_DURATION_S = 5.966666666666667;

export const KIMODO_SPRINT_LAUNCH_ENVELOPE = Object.freeze([
  0.07225362957858801,
  0.07225362957858801,
  0.14650437173974648,
  0.24248040701179635,
  0.3498072309753495,
  0.5166831226580241,
  0.5342212097340723,
  0.6684344121911941,
  0.7202867774932302,
  0.7202867774932302,
  0.7408702401846188,
  0.7560634647489939,
  0.8430514204992784,
  0.8430514204992784,
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
]);

export function sampleKimodoSprintEnvelope(raceTimeSeconds) {
  const t = Math.max(0, Math.min(
    1,
    Number(raceTimeSeconds) / KIMODO_SPRINT_SOURCE_DURATION_S
  ));
  const scaled = t * (KIMODO_SPRINT_LAUNCH_ENVELOPE.length - 1);
  const i0 = Math.floor(scaled);
  const i1 = Math.min(KIMODO_SPRINT_LAUNCH_ENVELOPE.length - 1, i0 + 1);
  const u = scaled - i0;
  return (
    KIMODO_SPRINT_LAUNCH_ENVELOPE[i0] * (1 - u) +
    KIMODO_SPRINT_LAUNCH_ENVELOPE[i1] * u
  );
}

export function computeKimodoLaunchVisualDrive(
  raceTimeSeconds,
  physicalSpeedRatio,
  blend = 0.55,
  source = "sprint"
) {
  const physical = Math.max(0, Math.min(1.2, Number(physicalSpeedRatio) || 0));
  const useAccel = source === "accel";
  const envelope = useAccel
    ? sampleKimodoAccelEnvelope(raceTimeSeconds)
    : sampleKimodoSprintEnvelope(raceTimeSeconds);
  const rawLead =
    raceTimeSeconds <= KIMODO_SPRINT_SOURCE_DURATION_S
      ? Math.max(0, envelope - Math.min(1, physical))
      : 0;
  const safeBlend = Math.max(0, Math.min(1, Number(blend) || 0));
  return {
    source: useAccel ? "accel" : "sprint",
    envelope,
    physicalSpeedRatio: physical,
    rawLead,
    appliedLead: rawLead * safeBlend
  };
}


// Explicit acceleration source generated in NVIDIA's official Kimodo Space.
export const KIMODO_ACCEL_SOURCE_DURATION_S = 5.966666666666667;
export const KIMODO_ACCEL_LAUNCH_ENVELOPE = Object.freeze([
  0.02897954465651384, 0.02897954465651384, 0.02897954465651384,
  0.02897954465651384, 0.02897954465651384, 0.02897954465651384,
  0.02897954465651384, 0.02897954465651384, 0.02897954465651384,
  0.05843513595988435, 0.12938796586895387, 0.20065224986399494,
  0.5597943545441499, 0.6066028410586989, 0.8428252949045213,
  0.8428252949045213, 0.8763663423105448, 0.8763663423105448,
  0.9838140385542465, 0.9838140385542465, 0.9838140385542465,
  0.9838140385542465, 0.9883791767668018, 0.9883791767668018,
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
]);

function sampleEnvelope(envelope, durationSeconds, raceTimeSeconds) {
  const t = Math.max(0, Math.min(1, Number(raceTimeSeconds) / durationSeconds));
  const scaled = t * (envelope.length - 1);
  const i0 = Math.floor(scaled);
  const i1 = Math.min(envelope.length - 1, i0 + 1);
  const u = scaled - i0;
  return envelope[i0] * (1 - u) + envelope[i1] * u;
}

export function sampleKimodoAccelEnvelope(raceTimeSeconds) {
  return sampleEnvelope(
    KIMODO_ACCEL_LAUNCH_ENVELOPE,
    KIMODO_ACCEL_SOURCE_DURATION_S,
    raceTimeSeconds
  );
}

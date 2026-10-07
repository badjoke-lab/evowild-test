import assert from "node:assert/strict";
import {
  sampleKimodoSprintEnvelope,
  computeKimodoLaunchVisualDrive,
  KIMODO_SPRINT_SOURCE_DURATION_S
} from "../../public/preview-motion-first/kimodo-launch-profile.js";

assert(sampleKimodoSprintEnvelope(0) > 0.07);
assert(sampleKimodoSprintEnvelope(2.3) > 0.8);
assert.equal(sampleKimodoSprintEnvelope(KIMODO_SPRINT_SOURCE_DURATION_S + 1), 1);

const baseline = computeKimodoLaunchVisualDrive(1.8, 0.35, 0);
const candidate = computeKimodoLaunchVisualDrive(1.8, 0.35, 0.55);
assert.equal(baseline.appliedLead, 0);
assert(candidate.rawLead > 0);
assert(candidate.appliedLead > 0);
assert(candidate.appliedLead < candidate.rawLead);

const done = computeKimodoLaunchVisualDrive(
  KIMODO_SPRINT_SOURCE_DURATION_S + 0.1,
  0.7,
  0.55
);
assert.equal(done.appliedLead, 0);

console.log("kimodo launch visual profile test: PASS");

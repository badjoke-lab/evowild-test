# Kimodo real upstream baseline review v0.1

Status: **parser/descriptor pipeline PASS; direct quadruped transfer NO-GO**

## Evidence now validated

The isolated lane has processed three real, official pre-generated Kimodo SOMA motions pinned to upstream commit `58e781898b3d7e328a676a75d3e338c45dce3ad9`.

- single prompt: run forward then leap;
- dense root path: slow casual walk;
- sparse root waypoints: moving hip-hop sequence.

The repository now stores reproducible provenance, source metadata, extracted summaries and timeseries under `experiments/kimodo-ardy/upstream-baselines/`.

The upstream example files use the older compact SOMA30 NPZ shape (`posed_joints`, `global_rot_mats`, `foot_contacts`). The extractor was corrected to recover the root from Hips and the heading from the SOMA30 hip axis. CI passes after this compatibility fix.

## What this proves

PASS:

- real Kimodo NPZ can be ingested without Kimodo installed;
- root speed, acceleration, stable body heading, turn rate and foot-contact timing can be extracted;
- the result can be converted into a normalized external-motion descriptor envelope.

NOT PROVEN:

- Kimodo can generate EvoWild quadruped motion;
- human absolute cadence/stance values improve S;
- humanoid joint rotations should be retargeted to S;
- the currently available upstream demo clips are suitable racing references.

## Current integration rule

Do not change `S_GAIT.stance`, stride length, leg phase offsets, or S joint rotations from these human values.

Only normalized transition shapes are eligible for the next experiment:

- root-speed transition shape;
- signed acceleration shape;
- signed heading/turn-rate shape.

The existing S controller remains authoritative for quadruped gait/contact semantics.

## Next gate

A useful C1 A/B test still requires a **pure running / sprint / acceleration Kimodo or ARDY source clip**, not the mixed run-and-leap example. Until that exists, this lane remains isolated and no Motion First production parameter is modified.

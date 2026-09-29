# Motion First Simplified Race Motion / Morph Readability v1 Review — 2026-09-29

Status: **PASS**

Scope:
- simplified Motion First 18-runner race
- dense-pack motion readability
- S / P / E / A proxy silhouette readability
- no high-detail / Hunyuan / Sakura / sprite / 2.5D / Lane 5 changes

## Dense-pack motion diagnosis

A fixed runner id was first reviewed and rejected as evidence because that runner had already broken away from the pack.

The review was repeated with the test selecting an actual current mid-pack runner by live race rank (target rank 7–11), then capturing four SIDE frames at 120 ms intervals.

Observed in real traffic:
- fore/hind limb phase changes remain visible
- stance vs recovery remains visible
- feet do not freeze into a sliding pose
- torso posture changes across the sequence
- neighboring runners retain independent gait phase rather than synchronizing into one animation

Decision:
- canonical gait amplitude does **not** need further exaggeration
- changing stride/contact amplitudes here would risk the already-passed stance/contact quality

## Morph readability diagnosis

P and A are already structurally distinct at race distance.

The remaining weak pair was S vs E:
- both read as light, narrow morphs
- the prior E proxy trunk was only slightly longer than S
- at SIDE race distance, the difference was too subtle

## Exact edit

E race proxy only:
- body longitudinal scale: `1.28 -> 1.40`
- pelvis longitudinal scale: `0.96 -> 1.05`

Fixed:
- E width
- E head
- E limbs / limb width
- leg pivots
- gait solver
- stance/contact
- stride
- chest/pelvis animation equations
- S / P / A geometry and motion

## Visual result

Final same-condition SIDE artifacts show:
- S: long-legged, narrow sprint silhouette with longer rear line
- E: visibly longer trunk, lighter horizontal endurance silhouette and shorter rear line
- P: compact heavy power build
- A: compact low agility build

The E change does not make E wider or heavier, so it does not drift toward P.

## Performance / regression evidence

Final CI:
- standard E2E: PASS
- Motion First capture: PASS
- Sakura NPR capture: PASS

Final performance sample:
- observed average FPS: `25.60`
- p95 frame time: `50.1 ms`
- average EvoWild JS work: `1.63 ms`
- p95 EvoWild JS work: `1.9 ms`
- render calls: `29`
- triangles: `36,724`
- proxy runners: `18`
- render pixel ratio: `0.75`

## Decision

**PASS**

Dense-pack motion is sufficiently readable without changing canonical gait amplitude.

The accepted implementation change is limited to strengthening E's long-trunk silhouette against S.

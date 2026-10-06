# S Authority Reset Review — current B2a-v5 baseline

Decision: **REJECT_CURRENT_BASELINE**

Primary authority:

`art/s-creature/references/00_s_type_modeling_image_v1.png`

Authority identity:

- 1448 × 1086
- 1,982,782 bytes
- SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`

Reviewed candidate:

`art/s-creature/output/S-vibe-b2a-v5.blend`

Reviewed views:

- `output/review/vibe-b2a-v5/S_vibe_b2a_v5_side.png`
- `output/review/vibe-b2a-v5/S_vibe_b2a_v5_front.png`
- `output/review/vibe-b2a-v5/S_vibe_b2a_v5_front34.png`
- `output/review/vibe-b2a-v5/S_vibe_b2a_v5_rear34.png`
- `output/review/vibe-b2a-v5/S_vibe_b2a_v5_back.png`

## Findings

### Global read — FAIL

The candidate still reads as a light deer/gazelle-like quadruped scaffold. The approved S sheet has a much more specific race-creature silhouette: strong plated shoulder/chest mass, deep waist tuck, streamlined but substantial pelvis, long angular limbs, paired long blade crests, split racing feet, and a long layered tail.

Continuing B2a shoulder-root micro-fairing would polish a baseline that is globally wrong.

### Head / crest — FAIL

Current:

- narrow blunt head;
- several thin near-parallel crest strips;
- side crest is too short, thin and uniform;
- front/back projection collapses toward narrow prongs.

Approved image:

- longer wedge-like head;
- two dominant elongated blade-like crest elements;
- broad visible blade surfaces;
- strong rear/upward sweep;
- clearly separated paired blades in front/back;
- smaller secondary blade structures around the skull base.

Required change: rebuild head/crest silhouette from the authority image. Do not preserve the old A1 crest as accepted geometry.

### Neck — FAIL

Current neck is too long, thin and tube-like through most of its length and rises too vertically.

Approved image keeps a long neck but gives it stronger base depth, a more integrated shoulder transition and a lower/faster forward racing posture.

Required change: lower/reshape the head-neck line and rebuild neck mass into the shoulder.

### Thorax / waist / pelvis — REVISE LARGE

KEEP concept:

- narrow waist;
- overall light body.

FAIL:

- shoulder/chest lacks the approved broad athletic plated mass;
- torso reads too smooth and weak;
- pelvis/upper hindquarter is too small and plain;
- body lacks the approved shoulder-to-waist-to-pelvis rhythm.

Required change: remass shoulder/thorax and pelvis before local root cleanup.

### Forelimbs / hindlimbs — REVISE LARGE

Current limbs are sufficiently long to remain a useful scale scaffold, but:

- fore/hind chains are too thin and generic;
- upper segments lack the approved athletic mass;
- angular joint language is underdeveloped;
- forelimb root artifact is not the highest-priority problem anymore.

Required change: preserve only rough length/stance landmarks if useful; rebuild segment mass and joint language later.

### Feet — FAIL

Current feet are small generic toe clusters.

Approved sheet shows a compact specialized split racing foot with two dominant prong/hoof-like contact structures and a very different silhouette.

Required change: rebuild feet from the FOOT STRUCTURE panel.

### Tail — HARD FAIL

Current tail is a plain narrow tube with a small blunt/upturned end.

Approved image shows a long lightweight tail with multiple layered blade/feather elements and a much larger aerodynamic envelope.

The earlier A4 decision that shortened the tail is invalidated by the exact authority image.

Required change: complete tail rebuild.

## Process consequence

The following old acceptances are invalid as final-authority approvals:

- A1 crest acceptance;
- A4 short-tail acceptance;
- A5/global acceptance derived from those assumptions;
- B0/B1/B2 work as evidence of final morphology correctness.

They remain useful only as technical modeling history.

## Next model

Create a new authority-driven silhouette baseline:

`output/S-authority-r0-v1.blend`

Technical donor use is allowed, but **no existing shape is protected merely because an earlier gate said KEEP**.

### R0 Gate order

1. R0-A1: head + paired dominant crest + neck line
2. R0-A2: shoulder/thorax + waist + pelvis mass
3. R0-A3: fore/hind limb segment rhythm
4. R0-A4: split racing feet
5. R0-A5: long layered tail
6. R0-A6: five-view global silhouette review

No Gate B micro-fairing resumes until R0-A6 passes against the exact authority image.

## Stop rule

Do not continue B2a-v5.

Do not start B2b.

The next modeling edit must be R0-A1 against the exact authority image.

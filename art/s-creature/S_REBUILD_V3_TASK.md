# EvoWild Run — S-rebuild-v3 Gate A Task

Status: READY
Scope: S only
Input: output/S-rebuild-v2.blend
Output: output/S-rebuild-v3.blend
Primary lock: S_MODELING_IMAGE_LOCK.md

## Gate A v2 decision

REVISE.

v2 is directionally better than v1 but still fails the locked silhouette in several major ways.

## Keep from v2

- Fresh rebuild basis; no v12 morphology.
- More rearward crest sweep in SIDE.
- Shorter tail.
- More compact torso.
- S-only Gate A scope.
- Multi-toe feet intent.

## Required v3 corrections

### 1. Crest / head — absolute first priority

Current failure:
- FRONT/BACK still read as a paired upright horn or arch.
- FRONT34 still shows crest plates too high and too vertical.
- Skull and crest root are not integrated strongly enough.

Required:
- Do not preserve the current front/back crest silhouette.
- Lower the vertical crest envelope substantially.
- Rotate major plate long axes further rearward so no plate axis approaches vertical from FRONT/BACK.
- Spread plate roots along the posterior-lateral cranium rather than stacking them into two vertical columns.
- In FRONT, the crest should read as layered lateral/rearward plates framing a narrow skull, not two prongs.
- In BACK, the crest should fan rearward and outward with visible overlap, not form a tall arch.
- Shorten or re-angle any plate whose projected FRONT/BACK height exceeds the skull-to-neck head height.
- Slightly broaden the posterior cranium and integrate each plate root into skull mass.
- Keep muzzle small and wedge-shaped.

### 2. Neck

Current failure:
- Still too straight, pipe-like, and upright.

Required:
- Shorten effective neck another 5–8% if needed.
- Add stronger base flare into shoulder/thorax while keeping upper neck light.
- Add a mild forward lean in SIDE so the head reads as a racing posture.
- Avoid a constant-width cylinder in FRONT/FRONT34.
- The dorsal line should flow from skull root to withers; the ventral line should merge into chest without a vertical tube read.

### 3. Shoulder / thorax / waist / pelvis

Current failure:
- Shoulder and thorax remain under-massed relative to the locked image.
- Torso still reads as a smooth narrow tube between limbs.

Required:
- Add compact shoulder/thorax depth and width without making a barrel chest.
- Establish a clearer withers/shoulder high point.
- Keep a narrow rising waist.
- Keep pelvis light but distinct, slightly elevated.
- SIDE must show an athletic rhythm: shoulder mass -> rising waist -> light pelvis.
- FRONT should show a narrow but real chest volume between forelimbs.

### 4. Limb joint silhouette

Current failure:
- Fore/hind limbs still read as rods.
- Difference between fore and hind joint chain remains weak.

Required:
- Forelimb: shoulder mass -> short upper segment -> compact elbow -> long narrow distal segment.
- Hindlimb: light hip/thigh mass -> forward knee -> rearward hock -> narrow distal segment.
- Increase silhouette angle changes at elbow/knee/hock, but keep sprint length.
- Do not add surface muscles or detail.
- Feet remain small multi-toed and light.

### 5. Tail / pelvis balance

Current failure:
- Tail length is improved but confirm it does not pull the silhouette rearward too much.

Required:
- Keep current shortened length unless balancing requires a small additional reduction.
- Preserve continuous taper.
- Terminal flare restrained.

## Forbidden

- single central horn
- paired upright horn silhouette
- antler structure
- deer/gazelle/horse body read
- tube neck
- barrel chest
- rod limbs
- hoof feet
- Cue Band
- eyes/details
- textures/colors
- animation
- final retopology

## Stop condition

After edits:
- save output/S-rebuild-v3.blend
- render exactly SIDE / FRONT / FRONT34 / REAR34 / BACK
- save to output/review/rebuild-v3/
- update CHECKPOINT.md and HANDOFF_STATE.json
- commit and push to feat/s-creature-model
- STOP for Gate A review

Do not proceed to Gate B.

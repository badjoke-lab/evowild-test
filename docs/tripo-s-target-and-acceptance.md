# EvoWild S — Target Authority and Tripo Acceptance Contract

Status: ACTIVE FOR TRIPO BENCH v0.2

This file exists to prevent two different questions from being mixed:

1. **What should the final S creature look like?**
2. **Can Tripo rig/animate an S-family quadruped well enough to be useful?**

They are not the same gate.

## 1. Final S morphology target

Authority lives in the dedicated S modeling lane, not in Tripo.

Primary morphology lock:

- `art/s-creature/S_MODELING_IMAGE_LOCK.md`

Repository reference family named by that lock:

- `art/s-creature/references/00_full_reference.png`
- `art/s-creature/references/01_s_body_primary.png`
- `art/s-creature/references/02_s_silhouette.png`

Supporting design references include the dedicated head/crest, leg/foot and tail sheets, but they do not override the primary S body/silhouette authority.

### Intended S read

S is a purpose-bred alien sprint racer.

It must read as:

- slim and fast;
- long-limbed;
- forward-balanced;
- athletic rather than bulky;
- clearly non-deer, non-horse and non-dog.

### Head / crest

Required:

- small, narrow wedge-shaped head;
- restrained muzzle / eye mass;
- skull-integrated crest;
- several overlapping rear-swept laminar plates/blades;
- compact aerodynamic rear/upward fan in side/3-quarter views;
- broad plate presence close to the sagittal plane in front/back views.

Hard fail:

- single central horn / unicorn spike;
- antler-like branching;
- paired horn towers;
- rabbit-ear plates;
- needle comb;
- straight sword-bundle crest;
- pasted-on crest disconnected from the skull.

### Neck

Required:

- long enough to preserve sprint posture, but not a tube;
- tapered toward the head;
- broadens smoothly into the shoulder girdle;
- sagittal depth sufficient to avoid a thin stalk;
- continuous dorsal and ventral transition into the thorax.

Hard fail:

- swan/deer neck;
- long cylindrical stalk;
- hanging ventral pouch;
- hard shelf into the chest.

### Torso / waist / pelvis

Required:

- compact athletic thorax;
- readable but restrained shoulder mass;
- ventral line rises behind the chest;
- clearly narrower/shallow waist;
- light elevated pelvis;
- continuous dorsal line.

Hard fail:

- barrel torso;
- long flat slab body;
- hanging sternum lobe;
- second bulky posterior barrel;
- disconnected shoulder cone.

### Limbs / feet

Required:

- long, light racing limbs;
- forelimb and hindlimb use visibly different joint rhythm;
- fore chain reads shoulder -> elbow -> wrist;
- hind chain reads hip -> knee -> hock;
- distal segments stay long and narrow;
- feet remain small multi-toed racing feet.

Hard fail:

- four rod-like legs;
- fore/hind chains with the same rhythm;
- hoof-like feet;
- paw-like heavy feet;
- bulky proximal cones dominating the torso.

### Tail

Required:

- high-set;
- light;
- aerodynamic;
- relatively short compared with the rejected long descending tail;
- carried mostly rearward near pelvis height;
- gently rises toward the tip;
- restrained blade/feather-like terminal broadening.

Hard fail:

- heavy club;
- long downward whip;
- blunt baton end.

### Proportion guardrails

Normalize shoulder-to-ground height to 1.00.

- head length: approximately 0.27–0.32
- skull width: approximately 0.16–0.20
- neck base-to-skull length: approximately 0.55–0.65
- torso shoulder-to-hip length: approximately 0.85–0.95
- thorax maximum depth: approximately 0.36–0.43
- waist depth: approximately 0.22–0.28
- crest rearward reach from skull root: approximately 0.45–0.60

These ranges prevent drift; they do not override the visual reference.

## 2. Current morphology status

The final production S is **not finished**.

The experimental Vibe lane has accepted its Gate-A global silhouette family, including local acceptance for head/crest/neck, torso/waist/pelvis, limb rhythm and tail.

Gate B anatomical massing is still open. In particular, shoulder-root / lateral-chest anatomical geometry remains under revision.

Therefore:

- do not call the current Vibe model production-final;
- do not call the old Hunyuan `source-lod2.glb` production-final;
- do not use a Tripo result to settle morphology.

## 3. Why Tripo currently uses source-lod2

Current Tripo T0 input:

`public/models/evowild-s/source-lod2.glb`

This is the older Hunyuan-derived unrigged S-family mesh from main.

Role in this bench:

**motion/rig feasibility carrier only**

It is chosen because:

- it is already a repository-resident unrigged quadruped-family mesh;
- it can test Tripo Auto Rig without contamination from the existing EvoWild rig;
- it is not waiting on unfinished Vibe Gate-B production topology.

A Tripo PASS on this carrier does not approve its silhouette.

Before production adoption, useful Tripo motion must be rerun or retargeted onto a morphology-approved rig-ready S asset.

## 4. T0 acceptance — rig compatibility only

T0 answers:

**Can Tripo produce a usable quadruped rig/export on the carrier?**

T0 must pass all structural checks:

- four limbs remain distinct;
- no neutral-pose knee/ankle/hock reversal or collapse;
- spine remains continuous;
- head and neck remain attached and usable;
- tail remains attached and usable;
- scale and orientation remain controllable;
- exported rigged asset re-opens successfully;
- skeleton/skin data exists.

T0 does **not** judge whether source-lod2 matches the final S reference.

## 5. T1 acceptance — basic motion feasibility only

T1 is one steady straight 5-second run.

T1 must be reviewed after export/replay, from:

- SIDE
- LOW
- CHASE
- FRONT
- continuous video

### Structural hard fail -> REJECT

Any one of these is enough to reject:

- missing animation after export;
- missing/broken skeleton or skin after export;
- limb inversion/collapse that recurs during the run;
- major self-intersection caused by the rig;
- head/neck detachment or catastrophic folding;
- tail detachment/catastrophic folding;
- axis/orientation failure that prevents controlled replay.

### Kinematic must-pass set

To reach T2, all of these must be usable:

- repeated grounded stance contacts;
- no persistent visible foot skating through stance;
- no persistent ground penetration/floating;
- coherent repeatable fore/hind phase;
- cadence and root travel can be mapped without rewriting the motion;
- shoulder/chest motion contributes to locomotion;
- pelvis/hind-leg drive contributes to locomotion;
- spine remains athletic rather than rigid or broken;
- vertical torso bounce is restrained;
- head/neck remains stable enough for racing readability.

### Decision mapping

`PASS_TO_T2`

Use only when:

- no structural hard fail exists; and
- the full kinematic must-pass set is usable; and
- any remaining issue is a normal runtime correction such as modest contact locking or root-speed remapping.

`KEEP_AS_REFERENCE`

Use when:

- structure/export is sound; but
- contact, phase, cadence or body mechanics would require substantial animation re-authoring rather than normal runtime correction.

`REJECT`

Use when:

- any structural hard fail exists; or
- the run is not recognizably controllable grounded quadruped locomotion.

## 6. S-specific motion style is a later gate

T1 is deliberately generic. It only proves basic Tripo locomotion feasibility.

Final S motion must later reinforce the morphology:

- forward-balanced sprint posture;
- long-limbed stride;
- strong hind-leg propulsion;
- compact athletic torso;
- restrained vertical bounce;
- stable forward head;
- motion that does not collapse into a default horse/deer/dog read.

A generic quadruped run may pass T1 and still fail final S adoption.

## 7. Primary-reference availability rule

The morphology lock says the approved “S-type Modeling Image v1.0” is the primary global target, while repository references are supporting constraints.

A later Vibe review also records that the separate Modeling Image v1.0 was not repository-accessible in that review context.

Therefore, until the primary approved image is repository-accessible or the authority order is explicitly changed:

**no automated/repository-only process may claim final S morphology conformance.**

It may only claim conformance to the repository-accessible references and written lock.

# S Vibe Lane — Gate A4 Tail Reference Analysis

Status: LOCKED FOR A4-v1
Lane: exp/s-creature-vibe-modeling
Source model: output/S-vibe-a3b-v1.blend

## A3 closure

Gate A3 (fore/hind limb joint rhythm): ACCEPTED for the experimental lane.

Accepted source:
- output/S-vibe-a3b-v1.blend

## Reference authority

Primary:
- references/01_s_body_primary.png
- references/02_s_silhouette.png
- references/00_full_reference.png

Secondary:
- references/05_tail_variants.png

Important:
The repository does not assign S to a numbered T1-T6 variant.
Do not invent such an assignment.

## S tail read from the approved body reference

The S tail is:
- attached high at the pelvis
- light and aerodynamic
- substantially shorter/lighter than the current long descending tube
- carried mostly rearward at near-pelvis height
- gently curves upward toward the end
- terminal region has a restrained blade/feather-like widening
- not a heavy club
- not a long downward whip

## Current A3b tail problem

Current tail:
- extends too far rearward/downward
- carries too much cylindrical mass
- terminal end reads blunt/cut
- visually drags the silhouette downward instead of reinforcing sprint posture

## A4-v1 scope

Editable:
- core rings 15-19 only
- vertex ids 120-159

Hard fixed:
- core rings 0-14
- accepted crest
- accepted forelimbs
- accepted hindlimbs
- all feet/toes
- topology and vertex count

Single hypothesis:
Replace the long descending tail with a shorter high-carried aerodynamic tail and restrained terminal blade.

## A4-v1 target stations

Ring 14 is the fixed pelvis boundary.

ring 15:
- Y 1.15
- top Z 1.025
- bottom Z 0.915
- half-width 0.052

ring 16:
- Y 1.29
- top Z 1.035
- bottom Z 0.945
- half-width 0.043

ring 17:
- Y 1.43
- top Z 1.020
- bottom Z 0.950
- half-width 0.032

ring 18:
- Y 1.55
- top Z 1.055
- bottom Z 0.945
- half-width 0.038

ring 19:
- Y 1.66
- top Z 1.070
- bottom Z 0.995
- half-width 0.006

Intent:
- rings 15-17: narrow aerodynamic stem
- ring 18: restrained terminal blade broadening
- ring 19: tapered terminal cap
- tip rises slightly rather than dropping

## Acceptance

SIDE:
- tail is clearly shorter/lighter than A3b
- tail does not descend into the hind-leg area
- root integrates with fixed pelvis
- terminal blade is visible but restrained

FRONT / BACK:
- tail stays narrow
- no paddle/club width

FRONT34:
- tail reinforces fast elevated silhouette
- no visual collision with fixed hindlimbs

Hard validation:
- only core vertices 120-159 may change
- rings 0-14 exact-match source
- crest, all limbs and all feet exact-match source
- topology unchanged

Stop after SIDE / FRONT / FRONT34 / BACK.
Do not start A5 automatically until A4 is reviewed.

## A4-v1 decision

Decision: REVISE.

Keep:
- shortened high-carried tail trajectory
- removed long descending tube
- compact overall length

Problem:
- stem remains too thick/segmented in SIDE
- terminal reads as a horizontal baton/cut end
- reference S tail is lighter and finishes with a subtle upward blade

A4-v2 locked hypothesis:
- tail rings 15-19 only
- keep the A4-v1 shortened Y extent
- reduce stem cross-section
- progressively raise tail centerline toward the tip
- preserve a restrained blade broadening near ring 18
- taper ring 19 sharply

## A4-v2 decision

Decision: KEEP.

Observed:
- tail remains substantially shorter and higher than the rejected pre-A4 tail
- stem is lighter than A4-v1
- terminal trajectory rises instead of dropping into the hind-leg silhouette
- no non-tail geometry changed
- remaining faceted terminal cut/tip integration is deferred to Gate B massing

## Gate A4 closure

Decision: ACCEPTED for the experimental lane.

Accepted model:
- output/S-vibe-a4-v2.blend

A4 acceptance is local to `exp/s-creature-vibe-modeling`.

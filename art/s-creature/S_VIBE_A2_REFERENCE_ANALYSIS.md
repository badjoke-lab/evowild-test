# S Vibe Lane — Gate A2 Reference Analysis

Status: LOCKED FOR A2a
Lane: exp/s-creature-vibe-modeling
Source model: output/S-vibe-a1-v11.blend

## A1 closure

Gate A1 (head / crest / neck): ACCEPTED for the experimental lane.

Accepted source:
- output/S-vibe-a1-v11.blend

Why A1 is accepted:
- head remains small and wedge-like
- neck no longer reads as the original long thin tube
- crest no longer reads as paired horns, a central needle, rabbit ears, or a sword bundle
- FRONT shows a compact close plate pair
- SIDE / FRONT34 show rear-swept layered laminae
- BACK shows a central overlapping plate stack
- all non-crest geometry remained hard-locked during the crest iterations

A1 acceptance is local to exp/s-creature-vibe-modeling. Nothing is merged into feat/s-creature-model.

## A2 target from approved S references

Primary visual evidence:
- references/01_s_body_primary.png
- references/02_s_silhouette.png
- references/00_full_reference.png

Observed target:
- anterior thorax has readable athletic mass
- body does not read as a long flat tube/slab
- ventral line rises quickly behind the chest
- waist is visibly narrower and shallower than thorax
- pelvis remains light and elevated
- dorsal line stays continuous
- no barrel torso
- no hanging sternum pouch

## Current v11 torso problem

The current Gate-A cage reads too long and flat through the thorax-to-waist region.

Current fixed station family after A1:
- ring 7: neck base, fixed
- ring 8: anterior thorax / shoulder transition
- ring 9: thorax
- ring 10: posterior thorax / abdominal transition
- ring 11: waist
- ring 12+: pelvis / tail-side body, fixed for A2a

## A2 subdivision

A2 will not edit thorax, waist and pelvis simultaneously.

### A2a — thorax / waist massing only

Editable:
- core ring 8
- core ring 9
- core ring 10
- core ring 11

Hard fixed:
- rings 0-7 (accepted head/neck)
- accepted crest object
- rings 12-19 (pelvis/tail)
- all forelimb/hindlimb meshes
- all feet/toes
- topology and vertex count

Single hypothesis:
Increase anterior thorax mass while making the ventral contour rise more decisively into a narrow waist.

Do not change longitudinal Y station positions in A2a.
This pass changes cross-sectional mass only. Longitudinal compacting, if still needed, is a later isolated hypothesis.

### A2a target stations

Keep each station Y unchanged.

- ring 8: top 1.125 / bottom 0.735 / half-width 0.155
- ring 9: top 1.115 / bottom 0.710 / half-width 0.155
- ring 10: top 1.085 / bottom 0.820 / half-width 0.112
- ring 11: top 1.080 / bottom 0.895 / half-width 0.080

Intent:
- rings 8-9: stronger shoulder/thorax volume without barrel width
- ring 10: earlier abdominal lift
- ring 11: clear narrow waist
- preserve smooth boundary into fixed ring 7 and fixed ring 12

## A2a acceptance

SIDE:
- chest is readable as athletic mass
- belly rises behind chest
- waist is clearly lighter
- no hanging sternum lobe
- no shelf/fold at ring boundaries

FRONT / FRONT34:
- chest gains mass without becoming barrel-shaped
- waist narrows visibly
- no smile-crease or pinched fold
- fixed limbs remain correctly related to the body

Hard validation:
- only vertices 64-95 (rings 8-11) may change
- all other core vertices exact-match source
- accepted crest exact-match source
- all appendage vertices exact-match source
- topology unchanged

Stop after SIDE / FRONT / FRONT34 / BACK renders.
Do not start A2b automatically.

## A2a-v1 decision

Decision: KEEP.

Observed:
- SIDE chest-to-abdomen-to-waist line is more athletic.
- ventral contour rises earlier behind the chest.
- FRONT / FRONT34 do not become barrel-shaped.
- no new sternum smile-crease or fold.
- longitudinal Y positions remain untouched, so the improvement is attributable to cross-sectional massing.

Accepted A2a source:
- output/S-vibe-a2a-v1.blend

## A2b — pelvis lightening only

Editable:
- core ring 12
- core ring 13
- core ring 14

Hard fixed:
- rings 0-11, including accepted A1 and A2a
- accepted crest
- rings 15-19 / tail
- all hindlimb and forelimb objects
- all feet/toes
- topology
- all Y station positions

Single hypothesis:
Raise and lighten the pelvis ventral mass while preserving a readable elevated hip.

Target stations:
- ring 12: top 1.130 / bottom 0.880 / half-width 0.105
- ring 13: top 1.120 / bottom 0.870 / half-width 0.112
- ring 14: top 1.060 / bottom 0.930 / half-width 0.078

Intent:
- preserve a mild elevated hip rhythm
- reduce the low hanging posterior belly/pelvis read
- keep hindquarter athletic rather than bulky
- do not move hindlimb roots in this pass

Acceptance:
- SIDE pelvis is light/elevated, not a second barrel
- waist-to-pelvis transition remains continuous
- hindlimb root relationship does not visibly break
- FRONT/BACK pelvis remains narrower/lighter than shoulder/thorax
- no fold/shelf appears at ring 11/12 or ring 14/15

## A2b-v1 decision

Decision: KEEP.

Observed:
- pelvis body is lighter and more elevated in SIDE.
- FRONT / BACK pelvis remains narrower than thorax.
- no new fold/shelf is introduced at the edited ring boundaries.
- the large hindquarter mass visible in FRONT34 is primarily the fixed hindlimb-root cage, not the pelvis core itself; limb-root language is deferred to Gate A3.

## Gate A2 closure

Decision: ACCEPTED for the experimental lane.

Accepted model:
- output/S-vibe-a2b-v1.blend

A2 acceptance is local to `exp/s-creature-vibe-modeling`; nothing is merged into `feat/s-creature-model`.

# EvoWild S QEM — tail morphology trial A, actual five-view review (2026-10-10)

**Verdict: topological deformation PASS for the 0.40 extension, but visual S-design gate REJECT. NOT game ready.**

## Locked source

- Exact highest-authority image: `art/s-creature/references/00_s_type_modeling_image_v1.png`; SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- TRELLIS2 QEM GLB: `S-trellis2-qem-repair-best.glb` SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
- Original 29,948 vertices, 59,932 faces and original source object remain unchanged. New test is a separate Blender object with a non-destructive shape key; no R0/R1 substitutes, no mesh topology added.
- Actual side/front/front34/rear34/back original/variant 10-render contact sheet: `tail-morph-a-v1/review/REAL_QEM_TAIL_A_FIVE_VIEW_COMPARE.jpg`.
- Blender source: `tail-morph-a-v1/S-QEM-real-tail-morph-a-v1.blend`; full numeric results: `tail-morph-a-v1/TAIL_MORPH_A_GEOMETRY_QA.json`.
- Actions [38030921640](https://github.com/badjoke-lab/evowild-test/actions/runs/38030921640): job SUCCESS (a numerical quality test, not S visual approval).

## A/B measurements

| Distal existing-tail extension | Measured tip gain | Face area >2x | Face flips/collapses | Geometry verdict |
| --- | --- | --- | --- | --- |
| +0.56 | +0.5573 | 436 | 0 / 0 | FAIL |
| +0.40 | +0.3980 | 0 | 0 / 0 | PASS local shape-key geometry only |

At +0.40, 764 existing vertices moved (359 with strong influence), no triangle shrank to under 0.5x or exceeded 2.0x area; max triangle area ratio 1.8241. No new triangle or separated mesh pieces.

## Actual visual review (5-view contact sheet opened)

The tail is recognizably longer, but remains **a single nearly featureless tapering rod/spur**. It still lacks the authoritative S's long multi-blade, segmented, feather-like armored tail and proper integrated thickness. Back/side views do not establish correct segmentation. Extending the short original stub further (0.56) is geometrically unsafe. The specimen also retains its excessively arched/narrow torso and rough leg-foot structure.

**Decision: REJECT_DESIGN**. Do not import the trial into game, do not transfer earlier IK/stride PASS to this geometry, do not claim visual authority match. This is a valid constraint/salvage experiment, not a finished tail.

## Correct next step

To reproduce layered tail plates, a versioned tail *topology/rebuild* is needed; merely stretching the donor's sparse stub cannot create the necessary articulated geometry. Keep the original source and all failed variants in separate layers and preserve exact source comparison. Re-test real rig deformation, contact and 3-cycle animation after any actual topology/shape change. Body, head/crest and limbs also remain visual REVISE/REJECT; do not merge S production.

# S Vibe B1b-v2 locked single hypothesis

Status: LOCKED BEFORE EDIT
Lane: exp/s-creature-vibe-modeling
Decision prerequisite: B1b-v1 REVISE, actual-image review in S_VIBE_B1B_V1_REVIEW.md.

source: output/S-vibe-b0-v025.blend. v1 is safe but its visible effect is insufficient; avoid cumulative deformation from an unaccepted model. This is a B1b alternative, not a restart of closed B1a.

target: lateral shoulder-root/chest-side raised ridge visible in FRONT34. Original-coordinate mask Y[-0.12,0.18], Z[0.80,1.12], |X|>=0.055. Retain margins Y/Z=0.045.

keep_fixed: every body Y/Z coordinate; X of every non-mask vertex; crest; all toes; all object topology, vertex/edge/polygon counts; cameras and render settings. No neck/torso-length/limb placement edits.

exact_edit: replace v1's alternating positive/negative X fairing with four positive inward-only passes at lambda 0.32 using the same-side immediate adjacency. For each vertex, compute max(0, |X|-mean neighbor |X|), reduce only this outward residual by lambda*boundary_weight, and cap cumulative inward movement at 0.012 from source. No negative pass, no outward filling, no other anatomical hypothesis.

expected_visual_change: reduce the localized shoulder cap/ridge in FRONT34 so it belongs more naturally to the lateral thorax while preserving readable shoulder mass. FRONT/BACK stay athletic/narrow. SIDE silhouette stays invariant because every Y/Z is fixed; SIDE lighting can change with surface normals. This hypothesis is unvalidated until the five-view actual-image review.

hard_limit: max inward |delta X|<=0.012 (float tolerance 1e-8); outward movement=0; whole-body X extent drift<=0.006; sagittal-plane crossing=0; all fixed-coordinate and topology comparisons exact. The larger local budget is declared because v1's <=0.006 budget plus negative pass gave insufficient visual plane change. Report saturation count; cap is part of the declared method, never silent scope expansion.

Stop: edit -> hard-scope assertions -> save -> five original views -> render hash assertions -> actual-image review. Fail any limit before rendering; do not compensate by widening scope. B2 and later remain blocked. Never accept from validation alone.

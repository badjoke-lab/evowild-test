# D1-B — rolling support candidate, validation in progress

D1-A was published at f148496/checkpoint5a7b661 before this implementation. Open `s-run-review.html?rig=contact-v3&toe=roll-v1` for the candidate; omit `toe` for the unchanged C1/C2 flat-contact baseline. All GLBs remain immutable.

The candidate rotates existing terminal joints around the lower support envelope of the D1-A actual mesh vertices. Fore terminal foot and hind toe chains are solved separately; C1/C2 anchors, integration and recovery paths remain intact. Fore maximum pitch22°, hind28°. Whole distal surfaces including the blended margin are independently checked for penetration. Early stance retains flat support; later support follows mesh vertices. Early recovery returns pitch to0 smoothly while preserving the original .48m rear recovery target.

Vertex changes use zero angular velocity/acceleration endpoints. The initial angular-time allocation produced a new velocity-regression failure (right front ~.031m/s vs unchanged .02m/s bound). Extending fore roll time reduced this to~.0216m/s, still FAIL. The current revision apportions each facet's rotation duration by sqrt(angle span) to distribute angular acceleration. **Final regression and graphics review are pending; no PASS/KEEP claim at this checkpoint.** [Initial failure log](initial-velocity-failure.log).

All old tests and thresholds remain unchanged. New tests separately measure legacy all-patch movement and actual active-support-vertex slip, so airborne heel movement is not treated as a planted foot slip. The legacy flat mode remains testable; the new opt-in mode also runs all rates, C2 speed profiles, zero-time switches, support boundaries, lift-off and freeze assertions.

This intermediate save meets the maximum checkpoint interval. Next: rerun `scripts/measure_s_toe_roll.mjs --after-only`, new toe plus unchanged C1/C2 regression tests, then complete the before/after four-view capture and visual verdict. Existing partial frames/measurements in the worktree are not final evidence and are not included in this checkpoint. No production promotion.

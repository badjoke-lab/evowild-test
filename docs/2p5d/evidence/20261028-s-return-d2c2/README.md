# D2-C2 — deterministic native pose and matched return

**Interim source checkpoint: implementation and real four-view capture saved; final combined regressions pending. REVISE, no production adoption.** C1 diagnostics were separately pushed at `4013beb7369af12122c001cd3e794ec8705c1ef2`.

Explicit review candidate: `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v2`. D2-A `toe=roll-v2` and D2-B `toe=roll-v2&body=push-v1` remain unchanged/selectable. No GLB, mesh, rest pose, manifest, ground, camera, race or Agent change.

`push-v2` evaluates both native base and advanced channels explicitly into Float64 buffers, so same-time evaluations cannot repeatedly blend a mutated bone and interpolant Float32 rounding does not dominate tiny-time velocity differences. All22 channels (seven native bones and their animated armature parent) remain coherent. Return occupies the SAME .44–.62 window and uses a quintic Hermite connection between existing endpoint poses with their first/second derivatives; quaternion components are hemisphere-aligned then normalized. No reduced phaseLead/amplitude or longer exit, no invented bob or physical-force claim. IK still runs after body pose using the existing anchors.

`roll-v3` retains actual support vertices and pitch/path, reducing only the compact vertical rounding width from3 to1.5mm. The resulting positive clearance remains explicitly measured, not hidden by translating ground/root or penetrating the mesh. Legacy v2 defaults are intact.

[Body-only tests](body-only-tests.log):8/8 PC/Pixel7 PASS with unchanged legacy thresholds and added.01m/s target. [Clearance boundary probe](clearance-probe.json): all rates, gap~.425mm and worst velocity residual~.00395m/s. Build PASS. Final combined seven-profile/old-suite tests are running, not yet claimed complete.

Four `after-*-return-slow16x.mp4` clips and [frames](frames/) match [C1 before](../20261028-s-return-d2c1/) at.005-cycle increments from.40 to.66. Simulation480Hz, playback30fps,16x slow motion. [PC](desktop-after.png), [Pixel7](android-after.png), actual browser page errors0. Full-cycle/speed-change comparison and final numerical/visual decision pending.

Next: finish targeted C1/C2/D1/D2 regression on both devices, compare final metrics/actual motion, preserve immutable assets, publish final evidence and remote verification. S remains REVISE.

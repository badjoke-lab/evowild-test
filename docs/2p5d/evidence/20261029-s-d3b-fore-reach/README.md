# D3-B recovery — source checkpoint

**Correction implemented; final regression/video review still running. Visual REVISE, not production.** Diagnosis was separately pushed at5d11ead. See [root cause](DIAGNOSIS.md) and [reproduced original failure](reproduced-failure.log).

Only push-v5 gains a persistent critically damped posture-rate state. It carries position and velocity through speed commands, is initialized to the requested diagnostic speed on seek, and freezes with speed0. C1 effective rate, cadence, distance, anchors and original swing replanning remain unchanged. The same posture rate drives the fore swing and chest gain; steady-speed amplitudes are identical to the previous push-v5. There is no global bob, amplitude removal, GLB edit or D2-D splice change.

[Actual mesh before microprobes](failed-speed-probes.json) / [after](fixed-speed-probes.json) separate the fore extension failure at.405061 from the chest failure at.75. The residual now decreases with the observation interval; dt0 positions remain fixed. BuildPASS. All14 focused D3-B/D2-D cases pass on both devices. All22 relevant contact/sole/roll cases also pass (21 plus one unchanged-timeout isolated retest13.2s). Four-view full-cycle/still capture remains to finish. See NUMERICAL_REVIEW.md and saved test logs.

Baseline `?rig=contact-v3&toe=roll-v3&body=push-v3`; corrected experiment `body=push-v5`. The old failed implementation remains recoverable at ca1c41d/5d11ead; v3/v4 stay selectable. Do not label the current visual quality KEEP merely from numerical tests.

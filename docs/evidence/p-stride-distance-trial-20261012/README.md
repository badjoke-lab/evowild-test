# P 2.5D: distance-clock trial — not a foot-lock solution

**Hypothesis:** Existing P cadence uses speed in a clamped nonlinear formula, while its world position keeps advancing according to speed. This changes projected ground travel per visual gait cycle during acceleration and at speeds above the clamp. A P-only trial mode ties pose advance to actual distance.

Use `race-quality.html?selected=2&pStrideClock=distance`. Default behavior is **unchanged** without the query parameter. S/E/A and all approved images are untouched. The calibration matches the old P cycle distance at 34 m/s, approximately 15.23 m/cycle.

The test measures phase advancement vs runner distance in a real Playwright race. **It does NOT measure individual toe motion** and cannot establish physically realistic stride length or foot locking. A 12-frame all-body sprite has no independent foot placement, so stance slip can remain even if this trial is green. Do not promote this mode without frame-by-frame visual review and actual rendered toe/ground tracking.

Existing canonical `P.webp`, improved 12-phase `p-run-sheet.webp`, and other morph animations remain unmodified. CI broad suite's known race-agent failures must be separated from this trial.

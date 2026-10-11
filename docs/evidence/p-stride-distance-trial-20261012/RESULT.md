# P 2.5D distance-phase trial — actual CI outcome

**Engineering experiment PASS; shape, sole-slip and production adoption NOT APPROVED.**

- Branch: `fix/2p5d-p-canonical-20261011`; implementation commit: `3103cb892c732f4f8d0e965eb7561978015d24ca`.
- Dedicated Actions run: https://github.com/badjoke-lab/evowild-test/actions/runs/38150705085 (SUCCESS).
- Playwright desktop and Android emulation both passed; measured ~15.23 m / pose cycle with a maximum phase-to-distance calculation error of 0.0420 m (desktop) and 0.0347 m (Android emulation).
- **Coverage limitation:** measured speed range only ~27.26–27.64 m/s, so varied speed cases still need coverage.
- Default race mode, existing 12-phase P WebP, S/E/A assets, reference image, and main are unchanged. The experiment is enabled only by `?pStrideClock=distance`.

This checks an **integrated distance clock** and its arithmetic, not actual rendered toe translation. The projected support foot still has no independent anchor. Do not claim foot slip was fixed; test a real toe/ground tracker and visually compare the resulting race clip before considering a production rollout. If it does not help, discard the experiment without altering the original 12 poses.

The broad CI build remains red from the existing Race Agent comparison failures, independent of this dedicated test's green result; causality of those failures still requires a controlled baseline rerun.

# Kimodo / ARDY feasibility experiment

This directory is an isolated motion-source experiment. Generated human/humanoid
motions are **not** production EvoWild assets and must not be directly retargeted
to the S quadruped.

## Tooling validation

Run:

    python -m pip install numpy
    python scripts/kimodo-ardy/check_environment.py
    python tests/kimodo-ardy/test_extract_motion_signals.py

A non-CUDA machine is expected to make check_environment.py exit with code 2.
That means "not an inference host", not that the analysis tooling is broken.

## Kimodo GPU run

On a CUDA/NVIDIA host with Kimodo installed:

    scripts/kimodo-ardy/run_kimodo_baseline.sh

Default model: Kimodo-SOMA-RP-v1.1.

The runner generates five constrained source motions, exports SOMA BVH, and
writes root/contact signal JSON + CSV files.

## ARDY GPU run

Clone/install ARDY separately, then:

    export ARDY_DIR=/path/to/ardy
    scripts/kimodo-ardy/run_ardy_baseline.sh

For the actual interactive Gate A1, launch ARDY's demo and test continuous
target velocity, live speed changes, left/right steering, waypoint following,
and prompt transition while locomotion continues.

Only root/cadence/contact/turn descriptors may transfer into the existing
EvoWild quadruped controller. Direct humanoid-joint retargeting is out of scope.

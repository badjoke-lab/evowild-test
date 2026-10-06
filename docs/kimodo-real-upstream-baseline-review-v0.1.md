# Kimodo real upstream baseline review v0.2

Status: **real Kimodo generation PASS; quadruped-safe visual transfer candidate KEEP; direct retarget NO-GO**

## Evidence validated

The isolated lane has now processed both official pre-generated Kimodo SOMA examples and a newly generated pure sprint from NVIDIA's official public Kimodo Space.

Generated sprint:

- prompt: `A person sprints forward quickly at a steady pace.`
- checkpoint display: `Kimodo-SOMA-RP-v1`
- duration: 6.0 s
- source: NVIDIA official public Kimodo Hugging Face Space
- stored under: `experiments/kimodo-ardy/space-generated/sprint-v1/`
- motion SHA-256: `355eaef4335c44f82a3473ac2159b6f4f13b921c7c443ea5af6fd40ddff92c6e`

The repository stores the raw generated NPZ, provenance, metadata, extracted signal summary/timeseries, transfer profile, and generation screenshot/debug record.

## Transfer restriction

The Kimodo skeleton is human/humanoid and EvoWild S is quadruped. Therefore:

- do not copy human joint rotations;
- do not copy absolute human cadence;
- do not copy human stance ratio;
- do not map two human feet onto four S legs;
- do not change race physics from human absolute speed.

Eligible transfer is restricted to normalized motion-shape information:

- launch/root-speed establishment shape;
- signed acceleration shape;
- signed heading/turn-rate shape.

The existing S gait solver remains authoritative for quadruped phase, contact, IK, stride and species identity.

## Sprint signal result

The generated sprint contains 180 frames at 30 Hz over 5.967 s.

Extracted reference values:

- horizontal distance: 6.221 m;
- mean root speed: 1.040 m/s;
- max root speed: 1.408 m/s;
- dominant vertical root frequency: 2.333 Hz;
- human contact/cadence measurements are retained for reference only and are blocked from direct S transfer.

The useful result is not the absolute speed. The normalized launch envelope establishes pace materially earlier than the current EvoWild launch presentation.

Comparison against the existing EvoWild launch shape:

- launch-envelope RMSE: **0.3142**;
- Kimodo 80% establishment: **2.214 s**;
- current EvoWild simulated 80% establishment: **3.762 s**.

## Deterministic C1 visual A/B

A visual-only candidate was added behind the query flag `kimodoLaunch=1`.

Important: the race target-speed calculation, damping, distance integration and gait phase remain unchanged. The Kimodo envelope only contributes a bounded launch-presentation bias to S body/chest/pelvis attitude.

The A/B harness freezes the fixed-60-Hz simulation at exactly **2.100 s** for both baseline and candidate.

Deterministic metrics:

| Metric | Baseline | Kimodo candidate |
| --- | ---: | ---: |
| race time | 2.100 s | 2.100 s |
| physical speed ratio | 0.3153 | 0.3153 |
| normalized Kimodo envelope | 0.7547 | 0.7547 |
| applied visual lead | 0.0000 | 0.2417 |
| S body pitch | -0.07058 rad | -0.09407 rad |
| explicit pitch bias | 0 | -0.00967 rad |
| recorded max stance slip | 0.00191 | 0.00152 |

Evidence is stored under `artifacts/kimodo-ardy/launch-ab/`:

- `baseline-side.png`
- `candidate-kimodo-side.png`
- `baseline-low.png`
- `candidate-kimodo-low.png`
- `metrics.json`

The SIDE and LOW captures are now same runner, same fixed simulation time, same physical speed and same gait phase. The candidate reads as a modestly stronger early sprint commitment without changing race velocity or creating a contact-regression signal in this gate.

Decision: **KEEP AS ISOLATED VISUAL CANDIDATE**.

This does not authorize enabling it by default or merging it into production. It only clears the concept for further isolated testing.

## Next gate

Generate a dedicated Kimodo acceleration source clip:

`A person accelerates smoothly from a run into a full sprint.`

Then compare its normalized acceleration/launch shape against the steady-sprint source. If the explicit acceleration source confirms the same early-establishment pattern, test a revised visual envelope against the current KEEP candidate. If it contradicts it, retain the steady-sprint candidate only as an experiment and do not promote it.

ARDY remains a separate interactive/runtime research lane.

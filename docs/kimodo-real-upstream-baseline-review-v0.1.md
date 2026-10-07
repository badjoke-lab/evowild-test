# Kimodo real upstream baseline review v0.3

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

## Explicit acceleration source result

A second real Kimodo clip was generated from NVIDIA's official Space:

- prompt: `A person accelerates smoothly from a run into a full sprint.`
- checkpoint display: `Kimodo-SOMA-RP-v1`
- duration: 6.0 s
- motion SHA-256: `7bd6c8a658467b1a1c09565570a6e38839d51fb964d147d1adc2e9edeed41018`

This source is materially more appropriate than the steady-sprint clip for launch shaping. It stays below the current EvoWild physical launch envelope early, then establishes sprint pace faster in the middle of the launch:

- Kimodo acceleration-source 50% establishment: **2.278 s**
- current EvoWild 50% establishment: **2.718 s**
- Kimodo acceleration-source 80% establishment: **2.660 s**
- current EvoWild 80% establishment: **3.762 s**

That means the earlier steady-sprint experiment was too aggressive at the beginning of the launch. The explicit acceleration source is now the preferred isolated source; the steady-sprint source remains available only as a comparison control.

## C1 v2 acceleration-mechanics A/B

The revised candidate keeps race physics, gait phase, stride length and stance timing unchanged. The Kimodo acceleration lead only modifies bounded S presentation channels:

- forward body attitude;
- longitudinal chest/pelvis extension;
- slightly stronger hind-root travel during the active acceleration window.

Deterministic evidence is stored under `artifacts/kimodo-ardy/accel-mechanics-ab/` for SIDE and LOW at 2.1 s, 2.7 s and 3.1 s.

At **2.1 s** the source says there should be no extra launch commitment, and the candidate is effectively identical to baseline:

- physical speed ratio: **0.3153 / 0.3153**
- applied Kimodo lead: **0.0000**
- body stretch: **0.04383 / 0.04383**
- pitch bias: **0**

At **2.7 s** the acceleration source becomes active:

- physical speed ratio: **0.4955 / 0.4955**
- applied Kimodo lead: **0.0000 → 0.1910**
- body pitch: **-0.04167 → -0.06019 rad**
- body stretch: **0.03468 → 0.07594**
- max stance slip: **0.00373 baseline / 0.00357 candidate**

At **3.1 s** the effect remains bounded while physical motion stays identical:

- physical speed ratio: **0.6176 / 0.6176**
- applied Kimodo lead: **0.1423**
- body pitch: **-0.04196 → -0.05579 rad**
- body stretch: **0.01071 → 0.04145**
- candidate max stance slip: **0.00375**, below the experiment limit of **0.01**

Visual review of SIDE and LOW shows a modestly clearer forward/longitudinal sprint commitment without a contact break or obvious silhouette deformation.

Decision: **KEEP C1 v2 AS THE ISOLATED KIMODO CANDIDATE**.

This still does not authorize production enablement. The candidate remains behind `kimodoLaunch=1`; when the flag is used without an explicit source, it now selects the dedicated acceleration source. `kimodoLaunchSource=sprint` remains only for controlled comparison.

## Next gate

Kimodo C1 v2 is complete as an isolated acceleration-presentation candidate.

Next:

1. test the v2 candidate in full 18-runner pack context to ensure the S launch remains readable without becoming visually anomalous;
2. keep all race physics and quadruped contact semantics unchanged;
3. proceed to the separate ARDY lane for real-time target-velocity / steering transition research;
4. do not promote either system to production unless it survives the corresponding visual and runtime gates.

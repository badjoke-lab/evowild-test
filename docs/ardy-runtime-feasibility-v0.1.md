# ARDY runtime feasibility v0.1

Status: **A0 contract pinned / real A0.5 batch generation pending**

## Scope

This lane evaluates NVIDIA ARDY separately from Kimodo.

ARDY is relevant to EvoWild because it is autoregressive and explicitly supports
interactive target-velocity, steering/waypoint and streaming prompt transitions.
It is still a human/humanoid motion system, so the same hard rule applies:

**do not retarget ARDY human joint rotations directly to the S quadruped.**

Only normalized transition descriptors are eligible for transfer into the
existing quadruped controller/presentation layer.

## Pinned upstream

- repository: `nv-tlabs/ardy`
- upstream commit: `693f74d13b3d04a0a22ce127ee79c929dd89756b`
- default released Core model: `ARDY-Core-RP-20FPS-Horizon40`
- Core short-horizon model: `ARDY-Core-RP-20FPS-Horizon8`
- released G1 models: `ARDY-G1-RP-25FPS-Horizon52`, `ARDY-G1-RP-25FPS-Horizon8`

The official registry currently contains Core and G1 releases. The repository
README says SOMA is still forthcoming.

## Official output contract

Official `scripts/generate.py` saves NPZ output containing generated motion
arrays plus `fps` and `text`. The decoded output includes:

- `posed_joints`
- `local_rot_mats`
- `global_rot_mats`
- `root_positions`
- `foot_contacts`

This is compatible with EvoWild's existing external-motion signal extractor.
No production runtime dependency on ARDY is required.

## No-cost real baseline path

No NVIDIA-operated public ARDY inference Space has been established in this
lane.

A public third-party ZeroGPU Space, `cs686/ardy-motion-api`, exposes
`/generate_blender` and states that its human rig uses the official
`nvidia/ARDY-Core-RP-20FPS-Horizon40` checkpoint. Its export contains full
ARDY NPZ + BVH + metadata.

This host is **not authoritative** for ARDY behavior. It is acceptable only as
a no-cost A0.5 compatibility source. Provenance must always preserve:

- third-party inference host identity;
- official NVIDIA checkpoint identity;
- generated NPZ hash;
- exact prompt/seed;
- EvoWild extractor output.

A real result from this host can prove that our ARDY NPZ ingestion path works.
It cannot by itself prove the official interactive-demo performance envelope.

## Gates

### A0 — contract/schema

PASS when released model registry and NPZ contract are pinned and the EvoWild
extractor accepts an ARDY-compatible fixture.

### A0.5 — real batch source

Generate one deterministic Core motion through the third-party ZeroGPU host:

`A person accelerates smoothly from a run into a full sprint.`

Required outputs:

- NPZ;
- BVH;
- metadata;
- request/provenance;
- extracted signal summary/timeseries;
- normalized transfer profile.

PASS means the real NPZ is accepted and produces finite root/transition signals.

### A1 — interactive runtime

Still requires a real ARDY interactive execution path with:

1. continuous target velocity;
2. live speed increase/decrease;
3. left/right steering;
4. waypoint turn;
5. prompt transition while locomotion continues.

Record native FPS, model/horizon, replan settings, hardware and transition
artifacts.

A0.5 does **not** substitute for A1.

## Cost rule

Do not create a paid GPU job automatically. Free/public compute may be used only
for this isolated research lane, with provenance and host classification.

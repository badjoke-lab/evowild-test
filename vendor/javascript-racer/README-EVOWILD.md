# Upstream pseudo-3D racing base

Source: jakesgordon/javascript-racer
Upstream commit: 3e8a060b5900755db27f899612a74a77427c853e
License: MIT (see LICENSE)

Purpose in EvoWild Run:
- use the proven pseudo-3D road projection and segment renderer as the race-view foundation;
- replace the car/player sprite layer with EvoWild Run creature rendering;
- keep EvoWild race simulation / Race Agent logic separate from rendering;
- do not reuse upstream art/audio unless separately imported and verified.

This directory intentionally keeps the upstream source close to original so behavior can be compared before adaptation.

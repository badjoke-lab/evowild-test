# Motion First Simplified Race LOD v2 Review — 2026-09-28

Status: **FAIL — do not merge the current animated-proxy implementation**

Evidence:

- PR #61
- reviewed head before corrective work: `a855e523bd445dd3f2b35cf18039a5221f9bdb56`
- CI run `36327304821`
- artifact: `motion-first-race-visuals` / `10934506078`
- latest main baseline: `b8f1febd81418816b60765ae8a741493bf3d6cee`
- latest main build run: `36326401891`

## Gates

### Isolation — PASS

The simplified gait/race runtime still blocks the Hunyuan/high-detail S assets through `SIMPLIFIED_LANE`.
The PR does not add Hunyuan, Sakura, sprite, 2.5D, or Lane 5 assets to this lane.

### Runner/morph coverage — PASS

The race still deploys 18 runners and keeps S / P / E / A active.

### Canonical motion source — PASS

The proxy does not introduce a cheaper sine gait.
The full S/P/E/A locomotion state is still advanced and the far representation copies body, head, leg, and tail transforms from that canonical state.

### Visual resolution — IMPROVED BUT NOT ACCEPTED

The PR raises the simplified-race internal render ratio from 0.4 to 0.75.
The captured frames are visibly less coarse than the 0.4 baseline.

This improvement cannot be accepted while frame continuity collapses.

### Performance — FAIL

The PR raises the CI race target to 28 FPS, but run `36327304821` measured **14 FPS** at the gate.
The captured race artifact also shows runtime readouts around the low-to-mid teens in multiple shots.

The latest main baseline is not clean either: run `36326401891` measured **17 FPS** against its existing 20 FPS gate.

Therefore neither the current main implementation nor PR #61 satisfies the Motion First requirement that speed impression and gait remain smooth under 18-runner load.

### Proxy draw representation — FAIL

The v2 proxy is low-poly, but each far runner is still composed of many separate meshes:
chest, pelvis, head, crest, tail, four upper legs, and four lower legs.

That substantially limits draw-call savings. Low polygon count alone is not enough.

### Cue Band — FAIL

The far proxy omits the Cue Band.
The Motion First creature standard requires the Cue Band on every EvoWild runner, including simplified representations.

## Decision

Do **not** merge the reviewed `a855e523...` state.

Corrective direction:

1. keep the 0.75 render ratio for the next measurement;
2. keep full canonical gait simulation for all 18 runners;
3. keep focus/near runners as the existing articulated full simplified model;
4. replace far-runner per-object proxy meshes with shared instanced articulated proxy parts;
5. restore a visible proxy Cue Band;
6. preserve S/P/E/A silhouette profiles;
7. rerun the 18-runner FPS gate and visual artifact capture;
8. only then judge LOD pop, camera-cut exposure, morph readability, and motion continuity.

A green CI result alone will not close this review. The post-fix artifact must also be inspected.


## Corrective measurements

These measurements are part of the same FAIL investigation and do not change the review state by themselves.

| PR state | Representation | Full / proxy | Render calls | FPS evidence | Result |
| --- | --- | ---: | ---: | --- | --- |
| `a855e523` | per-runner low-poly proxy meshes | mixed | not instrumented | 14 FPS gate result | FAIL |
| instanced proxy only | 8 shared proxy draw parts | mixed | not yet isolated | 14 FPS gate result | FAIL |
| render-frame canonical pose | 8 shared proxy draw parts | 4 / 14 | 248 | 22 FPS HUD sample | improved, still FAIL |
| focus counted inside LOD budget | 8 shared proxy draw parts | 2 / 16 | 134 | 15 FPS HUD sample | noisy / still FAIL |
| focus-only full + stable window | 8 shared proxy draw parts | 1 / 17 | 78 | 13.56 FPS average, 83.4 ms p95 over 2.5 s | FAIL |

The stable-window result proves that simply reducing draw calls and the number of visible full-detail runners is not sufficient.

The remaining architectural waste is that far runners still solve the expensive full procedural hierarchy and only then copy those transforms into a proxy. The next corrective implementation therefore applies the **same reviewed S/P/E/A canonical pose functions directly to lightweight proxy rigs**. Race physics and gait phase remain fixed at 60 Hz. This removes hidden hierarchy work rather than simplifying the locomotion model.

The richer proxy revision also restores motion-readable structure that the first proxy omitted:

- low forward neck chain;
- three tail joints;
- upper / lower / cannon limb chain;
- split foot;
- Cue Band.

The post-change state remains **FAIL until both performance gates and visual artifact review pass**.

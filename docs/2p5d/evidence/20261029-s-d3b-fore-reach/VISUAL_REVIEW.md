# D3-B actual-frame review

Reviewed 2026-10-30 JST. **Continuity correction: limited KEEP. Overall S movement: REVISE.** This is an assistant review of actual saved WebGL sequences and matched before/after stills, not independent human acceptance or a physical-device playback claim. Eight MP4 files retain the real sequences for normal-speed looping.

Canonical S was viewed read-only from `exp/s-creature-vibe-modeling` commit `48b39d8b64aa5146dc2028876b448c3e884295e6`, path `art/s-creature/references/00_s_type_modeling_image_v1.png`. SHA256 matches `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`. It is absent from this child/main and was neither regenerated nor imported. This source change leaves the inherited candidate's head, crest, proportions, mesh and tail unchanged. Preservation does not approve inherited gray/split-crest rendering against canonical art.

|View and inspected examples|Observed improvement|Remaining defect / verdict|
|---|---|---|
|SIDE, matched .20 at 1x and .75 at 1.5x; cycle .31/.64/.97|Airborne forefoot reaches farther forward without moving its planted anchor; chest/support posture changes at .75.|Reach increment is modest relative to the silhouette. Shoulder/back still act as a stiff block, with leg cycling more prominent than forward drive. REVISE.|
|LOW, matched frame03 (.765), sequence06/12/18 (.89/.14/.39)|Feet separate from ground during recovery; support stays on the fixed plane. No gross new jump/fold is apparent.|Front-foot overlap limits reading of chest loading. Small torso pitch does not establish a convincing absorb-and-push sequence. Sub-mm contact claims come from mesh measurement. REVISE.|
|CHASE, matched frame17 (.348), sequence00/06/12|Hind recovery and alternating support remain present; no new silhouette discontinuity is visible.|Torso obscures much fore reach from behind. Neck/back posture changes little; legs cycle beneath a stiff body. REVISE.|
|REAR 3/4, matched .75; sequence00/06/12/18|Four-limb contact/recovery sequence is readable; added reach preserves S proportions.|Chest offset is subtle, without strong full-body stretch/compression. Upright trunk and narrow visible propulsion remain below mock01's sprint goal. REVISE.|

The Pixel 7 screenshot at .80 shows the complete creature and feet between existing overlays. PC/mobile emulation use the same candidate and phase; physical Android performance is unmeasured. No camera/ground move improved the judgment.

No clear new gross deformation was found in sampled views; this is narrower than proving every frame artifact-free. The repaired response adds slight pose-amplitude lag during acceleration; steady amplitudes remain intact, and boundary regressions measure actual sole/body vertices. This is an optional v5 tradeoff, not physical load simulation.

The major remaining defect is coordinated shoulder/elbow/chest motion, not another numerical epsilon. A separate authored-motion unit should make shoulder advance, elbow fold/reach and chest support timing coherent while preserving IK anchors and species silhouette. If the current rig cannot express that action, record the limitation in the separate Blender lane rather than add global bob, stretch the model, or increase reach until joints distort. This task does not modify that lane or promote the candidate.

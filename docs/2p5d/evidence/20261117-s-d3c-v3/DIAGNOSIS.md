# D3-C v3 cause isolation, before new authoring

Baseline fetched: `729ba4a47e5dbd11601beca421acae68427368b5`. Corrected v2 Actions43897785827 independently confirmed SUCCESS. v1/v2 assets and existing evidence were reused, not regenerated.

`measure_s_d3c_recovery.mjs` sampled 36 phases from .14 through .473 in SIDE and REAR_3_4, using the actual GLB surface vertices. `recovery-*-summary.json` and raw JSON include fore-foot coordinates relative to chest/root, shoulder/upper/lower quaternions, elbow angle, stages, D3-B reach, FK guide displacement, actual nearest foot-surface separation and projected sole bounding boxes. Screen boxes are a visibility proxy, not collision volumes. Diagnostic phase seeks are distinct from elapsed-time tests.

At phase .307, v2 first IK gives elbows L91.90/R85.86°, sole-surface centroid Y .356/.382m. The FK swing guide then adds Y .175/.299m and Z .086/.047m; final elbows become74.68/55.10° and centroidY .531/.681m. Across the measured window, minimum elbows are62.37/54.27°. Native upper/lower FK has162.55/164.89° at .307: the native fore clips do not represent the final solved posture.

Repeating IK with zero guide changes actual foot points by **0m**. It is not an accumulating double-IK drift. Removing D3-B foreReach while retaining the v2 guide yields73.52/54.45° elbows at .307: D3-B is not the deep-fold cause (maximum foot effect across the window~5.04cm). It remains unchanged.

The two stance offsets are .64/.72. At .307, L is already labelled EXTENSION while R is FLIGHT, but the broad v2 authored fold still raises both feet near the sternum. There is no diagnosed 3D foot collision: v2 nearest sampled foot-surface separation~23cm at .307, min21.20cm in the window, and centroid separation~43cm. SIDE projects these motions into a compact silhouette; REAR_3_4 sole boxes have zero overlap at .307 but the limbs cluster beneath the torso. Spreading feet laterally would treat the wrong problem.

One bounded v3 hypothesis: shorten and stagger the recovery-fold windows within the existing airborne interval, keep the leading limb moving into extension while the trailing limb folds, and advance the humerus during that unfolding. Use continuous value/slope endpoints and the existing stance anchors. Retain the same shoulder/body support timing and rear drive initially; inspect their coupling to the new recovery. Do not raise peak foot lift, increase angular amplitudes, move the ground/camera or rebuild D2-D/D3-B. V2 remains immutable and S visual quality remains REVISE until new evidence exists.

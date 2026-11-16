# D3-C v2 recovery and completion — review only

The prior environment was replaced before its local-only v2 work could be published (GitHub git/API returned account-suspended HTTP403 then). This session fetched the actual remote v1 head `aaebb78` and restored the documented final authoring, without regenerating v1. The restored independent GLB SHA256 is **6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0**, exactly matching the previous session's final asset. Lost logs and captures are not represented as present; fresh tests and actual five-view evidence follow this checkpoint.

v2 retains all 23 joints, mesh bytes, weights, bind matrices, materials and v1 native clip. It adds a full authored pose clip and cubic review tracks for scapular glide/rotation, humerus advance, elbow recovery, chest loading, pelvis push and head/neck/tail follow-through. `src/s_authored_drive.js` applies GLB poses; existing IK anchors govern stance, and forward kinematics of the authored arm/elbow guides swing. Full standalone pose animation still needs the runtime IK adapter for the measured contact behavior; it is not an offline IK-baked export.

Two previously diagnosed fixes are included: restore scapular rest translation each evaluation (no accumulated glide); author analytic scapular tangents (the v1 LINEAR shoulder key at .75 had a velocity corner). Fore humerus/elbow amplitudes retain the last visually refined 18/-34 degrees, not the earlier cramped 26/-42 trial. v1 and original GLBs remain intact; no source image, production manifest, race logic, other species or main changes.

Asset integrity and production build pass. Current WebGL smoke loads the actual 23-joint v2 and captures `restored-SIDE.png`. Full numerical and visual verdict pending at this recovery checkpoint; overall S remains REVISE.

Review URLs: v1 `?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v1`, v2 same with `shoulder=authored-v2`.

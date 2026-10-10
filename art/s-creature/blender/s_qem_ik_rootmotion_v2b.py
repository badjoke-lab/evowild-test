"""EvoWild QEM ROOT-MOTION contact stress test (not a running cycle).

Starts with the proven real 13-bone IK .blend; moves the armature root through
a short measured forward translation, locks stance feet in world coordinates,
and swings diagonal partners to new world positions. Measures actual skinned
mesh, not bones/IK targets. No replacement mesh, no retopology.
"""
from pathlib import Path
import bpy, math, numpy as np, json, hashlib
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/qem-deformation-gate-20261010"
V1 = BASE / "ik-contact-v1"
OUT = BASE / "rootmotion-contact-v2b"
REV = OUT / "review"
REV.mkdir(parents=True, exist_ok=True)
src = bpy.data.objects["QEM_PRESERVED_ORIGINAL"]
dst = bpy.data.objects["QEM_REAL_13BONE_WEIGHTED_TEST"]
arm = bpy.data.objects["S_QEM_JOINT_CHAIN_ARMATURE"]
v1 = json.loads((V1 / "REAL_IK_CONTACT_QA.json").read_text())
assert v1["gate"] == "PASS_LIMITED_IK_CONTACT"
assert len(arm.data.bones) == 13
assert len(src.data.vertices) == len(dst.data.vertices) == 29948
assert len(src.data.polygons) == 59932
assert any(m.type == "ARMATURE" and m.object == arm for m in dst.modifiers)
scene = bpy.context.scene
source = np.asarray([src.matrix_world @ v.co for v in src.data.vertices], dtype=np.float64)
signature = hashlib.sha256(source.tobytes()).hexdigest()
faces = np.asarray([tuple(f.vertices) for f in src.data.polygons], dtype=np.int32)
initial_normal = np.cross(source[faces][:,1] - source[faces][:,0],
                          source[faces][:,2] - source[faces][:,0])
initial_length = np.linalg.norm(initial_normal, axis=1)
valid = initial_length > 1.e-10
assert int(valid.sum()) > 59000
NAMES = ("FORE_L", "FORE_R", "HIND_L", "HIND_R")
GROUP_A = ("FORE_L", "HIND_R")
GROUP_B = ("FORE_R", "HIND_L")

def patch(side, ymin, ymax):
    idx = np.flatnonzero((side*source[:,0] > .155) &
                         (source[:,1] >= ymin) & (source[:,1] <= ymax) &
                         (source[:,2] < .285))
    assert len(idx) >= 50
    low = np.quantile(source[idx,2], .08)
    patchidx = idx[source[idx,2] <= low+.025]
    assert len(patchidx) >= 15
    return idx, patchidx

feet = {
    "FORE_L":patch(-1,-1.75,-.65),
    "FORE_R":patch(+1,-1.4,-.44),
    "HIND_L":patch(-1,1.62,2.30),
    "HIND_R":patch(+1,1.62,2.30),
}
ref = {
    name: {
        "xy": source[patch_idx,:2].mean(axis=0),
        "min_z": float(source[idx,2].min())
    } for name,(idx,patch_idx) in feet.items()
}

def evaluated():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    ob = dst.evaluated_get(deps)
    mesh = ob.to_mesh()
    try:
        return np.asarray([ob.matrix_world @ vert.co for vert in mesh.vertices], dtype=np.float64)
    finally:
        ob.to_mesh_clear()

# Explicitly retain all 13 actual deform bones, existing IK constraints and weights.
targets = {
    name: bpy.data.objects["IK_FOOT_TARGET_"+name] for name in NAMES
}
assert all(any(c.type == "IK" and c.chain_count == 3 and c.target == targets[name]
                   for c in arm.pose.bones[name+"_LOWER"].constraints)
           for name in NAMES)
scene.frame_set(1)
# Capture the V1 rest targets, then replace V1 keyframes only in this new file.
rest_targets = {name:Vector(targets[name].location) for name in NAMES}
for target in targets.values():
    target.animation_data_clear()
arm.animation_data_clear()
arm.location = (0.,0.,0.)
total_forward = .032  # -Y model forward; normalized body height ~2.55
lift = .026
micro_sweep = .006

def ease(u):
    return u*u*(3.-2.*u)

sequence = {}
for frame in range(1,18):
    scene.frame_set(frame)
    progress = (frame-1)/16.
    arm.location = (0., -total_forward*progress, 0.)
    requested = {}
    for name in NAMES:
        group_a = name in GROUP_A
        if group_a:
            swinging = frame>=10
            u = max(0., min(1., (frame-9)/8.))
            landing = -total_forward*ease(u)
        else:
            swinging = frame<=8
            u = max(0., min(1., (frame-1)/8.))
            landing = -total_forward*.5*ease(u) if swinging else -total_forward*.5
        swing_height = lift*math.sin(math.pi*u) if swinging else 0.
        swing_dy = -micro_sweep*math.sin(math.pi*u) if swinging else 0.
        desired = np.array(ref[name]["xy"],dtype=np.float64)
        desired[1] += landing + swing_dy
        desired_z = max(.001,ref[name]["min_z"]) + swing_height
        target = targets[name]
        target.location = rest_targets[name] + Vector((0,landing+swing_dy,swing_height))
        requested[name] = {
            "state": "SWING" if swinging else "STANCE",
            "desired_xy": desired, "desired_z": desired_z,
            "landing_shift": landing,
        }
    # World-space contact feedback across animated root and 3-link Blender IK.
    for _ in range(9):
        verts = evaluated()
        for name in NAMES:
            idx, contact = feet[name]
            cur_xy = verts[contact,:2].mean(axis=0)
            cur_z = float(verts[idx,2].min())
            desired = requested[name]
            e_xy = desired["desired_xy"] - cur_xy
            e_z = desired["desired_z"] - cur_z
            step = np.clip(.75*np.array((e_xy[0],e_xy[1],e_z)),-.010,.010)
            target = targets[name]
            target.location += Vector(tuple(float(x) for x in step))
    xyz = evaluated()
    ground = {}
    for name in NAMES:
        idx, contact = feet[name]
        desired = requested[name]
        minz = float(xyz[idx,2].min())
        patch_xy = xyz[contact,:2].mean(axis=0)
        drift = float(np.linalg.norm(patch_xy-desired["desired_xy"]))
        state = desired["state"]
        gate = "PASS" if (-.002 <= minz <= .006 and drift <= .01) else "FAIL"
        ground[name] = {
            "state": state,"min_z": minz,
            "desired_patch_xy": desired["desired_xy"].tolist(),
            "actual_patch_xy": patch_xy.tolist(),
            "stance_world_horizontal_error": drift,
            "stance_gate": gate if state=="STANCE" else "NOT_STANCE",
            "ik_world_target": list(targets[name].location),
            "landing_offset_y": float(desired["landing_shift"])
        }
        targets[name].keyframe_insert(data_path="location",frame=frame)
    arm.keyframe_insert(data_path="location",frame=frame)
    tri = xyz[faces]
    normal = np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    leng = np.linalg.norm(normal,axis=1)
    ratio = np.divide(leng,initial_length,out=np.ones_like(leng),where=valid)
    deformed = np.linalg.norm(xyz-source,axis=1)
    skin = {
        "flipped":int(np.count_nonzero((np.sum(normal*initial_normal,axis=1)<0)&valid)),
        "collapsed":int(np.count_nonzero((leng<1.e-10)&valid)),
        "below_half":int(np.count_nonzero((ratio<.5)&valid)),
        "above_double":int(np.count_nonzero((ratio>2)&valid)),
        "moved_vertices":int(np.count_nonzero(deformed>1.e-5)),
        "max_displacement":float(deformed.max()),
    }
    sequence[str(frame)] = {
        "root_world_y":float(arm.location.y),
        "foot_contacts":ground,
        "skinning":skin,
    }

# Reopen the 17 integer animation keys through Blender's depsgraph; results
# must survive serialization/keyframes, not just in-memory procedural solving.
replay = {}
for f in range(1,18):
    scene.frame_set(f)
    xyz = evaluated()
    replay[str(f)] = {}
    for name in NAMES:
        idx, contact = feet[name]
        a = sequence[str(f)]["foot_contacts"][name]
        replay[str(f)][name] = {
            "min_z":float(xyz[idx,2].min()),
            "patch_drift":float(np.linalg.norm(
                xyz[contact,:2].mean(axis=0)-np.asarray(a["desired_patch_xy"]))),
        }

after = np.asarray([src.matrix_world @ v.co for v in src.data.vertices],dtype=np.float64)
assert hashlib.sha256(after.tobytes()).hexdigest() == signature
assert len(arm.data.bones)==13
fail_ground = [(f,n) for f,frame in sequence.items()
               for n,d in frame["foot_contacts"].items()
               if d["state"]=="STANCE" and d["stance_gate"]!="PASS"]
fail_replay = [(f,n) for f,frame in sequence.items()
               for n,d in frame["foot_contacts"].items()
               if d["state"]=="STANCE" and not (
                    -.002<=replay[f][n]["min_z"]<=.006 and
                    replay[f][n]["patch_drift"]<=.01)]
fail_skin = [f for f,frame in sequence.items()
             if any(frame["skinning"][k]>0 for k in
                    ("flipped","collapsed","below_half","above_double"))]
swing_peaks = {
    n:max(frame["foot_contacts"][n]["min_z"]
          for frame in sequence.values()
          if frame["foot_contacts"][n]["state"]=="SWING")
    for n in NAMES}
swing_penetration = [(f,n) for f,frame in sequence.items()
                     for n,d in frame["foot_contacts"].items()
                     if d["state"]=="SWING" and d["min_z"] < -.002]
gates = {
    "stance_contact_with_moving_root":not fail_ground,
    "keyframed_replay":not fail_replay,
    "all_17_frames_safe_mesh":not fail_skin,
    "all_four_swing_peaks_above_0_012":all(z>=.012 for z in swing_peaks.values()),
    "swing_no_ground_penetration":not swing_penetration,
    "nonzero_armature_root_motion":abs(sequence["17"]["root_world_y"] -
                                         sequence["1"]["root_world_y"]) > .028,
    "original_13_bone_mesh_preserved":True
}
result = {
    "gate":"PASS_LIMITED_ROOT_MOTION_IK" if all(gates.values()) else "FAIL_ROOT_MOTION_IK",
    "experiment":"actual_QEM_13bone_root_world_motion_ground_lock_v2",
    "original_glb_sha256":v1["original_glb_sha256"],
    "original_qem_unchanged":True,
    "original_vertices":29948,"original_faces":59932,"bone_count":13,
    "body_travel_world_units":total_forward,
    "body_height_reference":2.55,
    "stride_lift_world_units":lift,
    "frame_count":17,
    "frames":sequence,"replay":replay,
    "fail_ground":fail_ground,"fail_replay":fail_replay,"fail_skin":fail_skin,
    "swing_peaks":swing_peaks,"swing_penetration":swing_penetration,"gates":gates,
    "race_gait":False,"physics_validated":False,"final_shape_approved":False,
    "production_asset":False,
    "scope_note":"A 17-frame world-space stance root-motion test with paired leg swing. It does not certify full gallop gait, cadence, cycle seams, impacts or a game-ready creature."
}
(OUT/"ROOT_MOTION_CONTACT_QA.json").write_text(json.dumps(result,indent=2)+"\n")

scene.frame_start=1;scene.frame_end=17;scene.render.fps=24
cam=scene.camera
cam.data.type="ORTHO"
cam.data.ortho_scale=5.05
c=Vector((0,-.025,1.275))
cam.location=c+Vector((1,-1,.23)).normalized()*9
cam.rotation_euler=(c-cam.location).to_track_quat("-Z","Y").to_euler()
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=800;scene.render.resolution_y=600
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
src.hide_render=True;dst.hide_render=False;arm.hide_render=True
for t in targets.values():
    t.hide_render=True
for f in range(1,18):
    scene.frame_set(f)
    scene.render.filepath=str(REV/("QEM_ROOT_IK_REAL_%02d.png"%f))
    bpy.ops.render.render(write_still=True)
scene.frame_set(9)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-13bone-rootmotion-v2b.blend"),compress=True)
print("QEM_MOVING_ROOT_CONTACT",json.dumps({
    "gate":result["gate"],"gates":gates,"failed_stance":fail_ground[:16],
    "failed_geometry_frames":fail_skin,"peaks":swing_peaks
},indent=2))

"""EvoWild S QEM: genuine four-foot IK/contact prototype.

Loads the existing 13-bone source .blend (29,948 / 59,932). Adds
nondeforming IK targets, solves stance and swing with feedback from
evaluated, skinned contact-patch vertices, and saves auditable evidence.
This is NOT a racing cycle or a production rig. Never substitute a mesh.
"""
from pathlib import Path
from math import pi, sin
import json, hashlib
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/qem-deformation-gate-20261010"
PREVIOUS = BASE / "three-segment-armature-v1"
OUT = BASE / "ik-contact-v1"
OUT.mkdir(parents=True, exist_ok=True)
REV = OUT / "review"
REV.mkdir(parents=True, exist_ok=True)
NAMES = ("FORE_L", "FORE_R", "HIND_L", "HIND_R")
src = bpy.data.objects["QEM_PRESERVED_ORIGINAL"]
dst = bpy.data.objects["QEM_REAL_13BONE_WEIGHTED_TEST"]
arm = bpy.data.objects["S_QEM_JOINT_CHAIN_ARMATURE"]
qa0 = json.loads((PREVIOUS / "13_BONE_REAL_ARMATURE_QA.json").read_text())
assert len(arm.data.bones) == 13 and qa0["rig_gate"] == "PASS_LIMITED_MULTI_JOINT_SKINNING"
assert len(src.data.vertices) == len(dst.data.vertices) == 29948
assert len(src.data.polygons) == len(dst.data.polygons) == 59932
assert len(dst.modifiers) and any(x.type == "ARMATURE" and x.object == arm for x in dst.modifiers)
donor = ROOT / "experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(donor.read_bytes()).hexdigest() == qa0["input_original_GLb_sha256"]

source = np.asarray([src.matrix_world @ v.co for v in src.data.vertices], dtype=np.float64)
source_hash = hashlib.sha256(source.tobytes()).hexdigest()
faces = np.asarray([tuple(p.vertices) for p in src.data.polygons], dtype=np.int32)
p0 = source[faces]
n0 = np.cross(p0[:, 1] - p0[:, 0], p0[:, 2] - p0[:, 0])
ln0 = np.linalg.norm(n0, axis=1)
valid = ln0 > 1.e-10
assert valid.sum() >= 59000

# Use exactly the same original source foot-vertex masks as the previous contact QA.
def foot_mask(side, lo, hi):
    idx = np.flatnonzero((side * source[:, 0] > .155) &
                        (source[:, 1] >= lo) & (source[:, 1] <= hi) &
                        (source[:, 2] < .285))
    assert len(idx) >= 50, (side, lo, hi, len(idx))
    low = np.quantile(source[idx, 2], .08)
    patch = idx[source[idx, 2] <= low + .025]
    assert len(patch) >= 15
    return idx, patch

feet = {
    "FORE_L": foot_mask(-1, -1.75, -.65),
    "FORE_R": foot_mask(+1, -1.4, -.44),
    "HIND_L": foot_mask(-1, 1.62, 2.30),
    "HIND_R": foot_mask(+1, 1.62, 2.30),
}
reference = {
    name: {"xy": source[patch, :2].mean(axis=0),
           "min_z": float(source[idx, 2].min()),
           "n_foot": len(idx), "n_contact": len(patch)}
    for name, (idx, patch) in feet.items()
}

# Remove the previous keyframed bend test from the NEW output, not from the
# tracked source .blend. The same 13 deform bones and vertex groups survive.
arm.animation_data_clear()
for pb in arm.pose.bones:
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)
    pb.constraints.clear()
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
before_ik_mesh = None

def evaluated_world():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    ob = dst.evaluated_get(deps)
    m = ob.to_mesh()
    try:
        return np.asarray([ob.matrix_world @ v.co for v in m.vertices], dtype=np.float64)
    finally:
        ob.to_mesh_clear()

before_ik_mesh = evaluated_world()
rest_error = float(np.max(np.abs(before_ik_mesh - source)))
assert rest_error < 1.e-4, rest_error

tips = {}
targets = {}
for name in NAMES:
    pb = arm.pose.bones[name + "_LOWER"]
    tip = arm.matrix_world @ pb.tail
    tips[name] = Vector(tip)
    target = bpy.data.objects.new("IK_FOOT_TARGET_" + name, None)
    bpy.context.scene.collection.objects.link(target)
    target.empty_display_type = "SPHERE"
    target.empty_display_size = .065
    target.location = tip
    target.hide_render = True
    targets[name] = target
    ik = pb.constraints.new("IK")
    ik.name = "REAL_THREE_LINK_FOOT_CONTACT_IK"
    ik.target = target
    ik.chain_count = 3
    ik.iterations = 100
    ik.use_stretch = False

bpy.context.view_layer.update()
rest_ik = evaluated_world()
initial_ik_error = float(np.max(np.abs(rest_ik - source)))

# Two alternating diagonal pairs, initially stationary in model coordinates.
# A planted foot is measured from its actual skin patch; targets are corrected
# until the evaluated vertices (not merely the IK empty) are near the ground.
# Root movement, speed, stride dynamics and true gait remain unimplemented.
scene = bpy.context.scene
scene.frame_start, scene.frame_end, scene.render.fps = 1, 16, 24
step_length = .020
step_lift = .026
correction_passes = 7
phase_offsets = {"FORE_L": 0., "HIND_R": 0.,
                 "FORE_R": .5, "HIND_L": .5}
sequence = {}

for f in range(1, 17):
    scene.frame_set(f)
    phases = {}
    for name in NAMES:
        phase = (((f - 1) / 16.) + phase_offsets[name]) % 1.
        swinging = phase >= .5
        progress = (phase - .5) * 2 if swinging else 0.
        # +Y is the model's rear direction, so -Y advances foreward.
        forward = -step_length * sin(pi * progress) if swinging else 0.
        lift = step_lift * sin(pi * progress) if swinging else 0.
        target = targets[name]
        target.location = tips[name] + Vector((0, forward, lift))
        phases[name] = {"state": "SWING" if swinging else "STANCE",
                        "lift_intent": float(lift), "forward_intent": float(forward)}
    # Solve on the REAL skinned foot patch, because bone tail lock alone does
    # not guarantee zero sole penetration with weighted ankle/tarsus geometry.
    for iteration in range(correction_passes):
        verts = evaluated_world()
        for name in NAMES:
            idx, patch = feet[name]
            ref = reference[name]
            cxy = verts[patch, :2].mean(axis=0)
            low = float(verts[idx, 2].min())
            swinging = phases[name]["state"] == "SWING"
            intended_xy = ref["xy"].copy()
            intended_xy[1] += phases[name]["forward_intent"]
            intended_minz = max(.001, ref["min_z"]) + phases[name]["lift_intent"]
            error_xy = intended_xy - cxy
            error_z = intended_minz - low
            # Damped local error correction, capped against runaway joints.
            correction = np.clip(.75 * np.array(
                [error_xy[0], error_xy[1], error_z]), -.012, .012)
            t = targets[name]
            t.location.x += float(correction[0])
            t.location.y += float(correction[1])
            t.location.z += float(correction[2])
    evaluated = evaluated_world()
    stats = {}
    for name in NAMES:
        idx, patch = feet[name]
        ref = reference[name]
        cxy = evaluated[patch, :2].mean(axis=0)
        low = float(evaluated[idx, 2].min())
        state = phases[name]["state"]
        # Stance truth: foot pinned in world coordinates, not moving target.
        drift = float(np.linalg.norm(cxy - ref["xy"]))
        stats[name] = {
            "state": state,
            "min_world_z": low,
            "horizontal_drift_from_original_patch": drift,
            "mean_patch_z": float(evaluated[patch, 2].mean()),
            "contact_patch_vertex_count": int(len(patch)),
            "intended_lift": phases[name]["lift_intent"],
            "ik_target_world": list(map(float, targets[name].location)),
            "contact_gate": (
                "PASS" if (-.002 <= low <= .006 and drift <= .01) else "FAIL"
            ) if state == "STANCE" else "NOT_STANCE",
        }
        targets[name].keyframe_insert(data_path="location", frame=f)
        targets[name].rotation_mode = "XYZ"
    triangles = evaluated[faces]
    n = np.cross(triangles[:, 1] - triangles[:, 0],
                 triangles[:, 2] - triangles[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ratio = np.divide(ln, ln0, out=np.ones_like(ln), where=valid)
    flipped = int(np.count_nonzero((np.sum(n0 * n, axis=1) < 0) & valid))
    collapsed = int(np.count_nonzero((ln < 1.e-10) & valid))
    small = int(np.count_nonzero((ratio < .5) & valid))
    large = int(np.count_nonzero((ratio > 2.) & valid))
    displacement = np.linalg.norm(evaluated - source, axis=1)
    sequence[str(f)] = {
        "feet": stats,
        "skinning": {
            "flipped_faces": flipped, "collapsed_faces": collapsed,
            "area_below_half": small, "area_above_double": large,
            "moved_vertices": int(np.count_nonzero(displacement > 1.e-5)),
            "max_displacement": float(displacement.max()),
        },
    }

# Verify all keyframed target positions through an evaluated replay
# (guards against a pose that only happened during the procedural solve).
replay = {}
for f in range(1, 17):
    scene.frame_set(f)
    actual = evaluated_world()
    replay[str(f)] = {
        name: {
            "low": float(actual[idx, 2].min()),
            "drift": float(np.linalg.norm(actual[patch, :2].mean(axis=0) -
                                           reference[name]["xy"])),
        } for name, (idx, patch) in feet.items()
    }

source_again = np.asarray([src.matrix_world @ v.co for v in src.data.vertices], dtype=np.float64)
assert hashlib.sha256(source_again.tobytes()).hexdigest() == source_hash
assert len(arm.data.bones) == 13
all_stance = [(f, name, r) for f, frame in sequence.items()
              for name, r in frame["feet"].items() if r["state"] == "STANCE"]
geometry_errors = [(f, frame["skinning"]) for f, frame in sequence.items()
                   if any(frame["skinning"][field] != 0 for field in (
                       "flipped_faces", "collapsed_faces", "area_below_half",
                       "area_above_double"))]
stance_fail = [(f, name) for f, name, r in all_stance
               if r["contact_gate"] != "PASS"]
replay_fail = [(f, name) for f, name, _ in all_stance
               if not (-.002 <= replay[f][name]["low"] <= .006 and
                       replay[f][name]["drift"] <= .01)]
swing_peaks = {
    name: max(sequence[str(f)]["feet"][name]["min_world_z"]
              for f in range(1, 17)
              if sequence[str(f)]["feet"][name]["state"] == "SWING")
    for name in NAMES
}
all_swing_above_ground = all(
    r["min_world_z"] >= -.002 for frame in sequence.values()
    for r in frame["feet"].values() if r["state"] == "SWING")
all_actually_moved = max(f["skinning"]["max_displacement"]
                         for f in sequence.values()) >= .01
gates = {
    "stance_patch_contact": not stance_fail,
    "baked_replay_stance_contact": not replay_fail,
    "all_frame_triangle_quality": not geometry_errors,
    "swing_clearance": all(v >= .012 for v in swing_peaks.values()) and all_swing_above_ground,
    "not_trivial_zero_motion": all_actually_moved,
    "original_source_preserved": True,
    "thirteen_original_deform_bones": len(arm.data.bones) == 13,
}
overall = all(gates.values())
report = {
    "experiment": "actual_QEM_13_bone_four_foot_ik_contact_v1",
    "input_blend": str(PREVIOUS / "S-QEM-real-13-bone-joint-chain-test.blend"),
    "original_glb_sha256": qa0["input_original_GLb_sha256"],
    "vertices": 29948,
    "faces": 59932,
    "deform_bones": 13,
    "ik_targets": list(targets.keys()),
    "ik_solver": "Blender IK constraint, 3-bone chains, evaluated-foot-patch error feedback",
    "root_motion": False,
    "race_gait": False,
    "approved_production": False,
    "original_source_mesh_modified": False,
    "rest_skinning_error_before_ik": rest_error,
    "initial_ik_rest_max_coordinate_change": initial_ik_error,
    "swing_step_length": step_length,
    "swing_lift": step_lift,
    "contact_gate_bounds": {
        "min_z": [-.002, .006], "max_stance_horizontal_drift": .01,
        "min_swing_peak_lift": .012
    },
    "frame_data": sequence, "replay_data": replay, "swing_peak_min_z": swing_peaks,
    "stance_failures": stance_fail, "replay_failures": replay_fail,
    "geometry_fail_frames": [f for f, _ in geometry_errors],
    "gate_checks": gates,
    "gate": "PASS_LIMITED_IK_CONTACT" if overall else "FAIL_IK_CONTACT",
    "note": "Stance contact / brief swing rehearsal ONLY; not a physically-based gait, rooted race cycle or final S shape approval."
}
(OUT / "REAL_IK_CONTACT_QA.json").write_text(json.dumps(report, indent=2) + "\n")

# Save genuine Blender source with the same QEM mesh; sample-render all 16
# keyed IK target frames for visual inspection.
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 4.8
center = Vector((0, 0, 1.275))
cam_offset = Vector((1, -1, .25)).normalized() * 9
scene.camera.location = center + cam_offset
scene.camera.rotation_euler = (center - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
src.hide_render = True
dst.hide_render = False
arm.hide_render = True
for name in NAMES:
    targets[name].hide_render = True
for f in range(1, 17):
    scene.frame_set(f)
    scene.render.filepath = str(REV / ("QEM_IK_REAL_%02d.png" % f))
    bpy.ops.render.render(write_still=True)
scene.frame_set(8)
bpy.ops.wm.save_as_mainfile(
    filepath=str(OUT / "S-QEM-real-13bone-IK-contact-v1.blend"), compress=True
)
print("QEM_IK_GROUND_CONTACT_RESULT", json.dumps({
    "gate": report["gate"], "checks": gates,
    "stance_failures": stance_fail[:16], "replay_failures": replay_fail[:16],
    "geometry_fail_frames": report["geometry_fail_frames"],
    "swing_peaks": swing_peaks,
}, indent=2))

import bpy
import json
import math
import sys
from pathlib import Path

from mathutils import Vector, Matrix

argv = sys.argv
sep = argv.index("--")
asset_path = Path(argv[sep + 1])
signals_path = Path(argv[sep + 2])
out_dir = Path(argv[sep + 3])
out_dir.mkdir(parents=True, exist_ok=True)

signals = json.loads(signals_path.read_text(encoding="utf-8"))
sig = signals["signals"]

# ---------- scene ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(asset_path))

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 480
scene.render.resolution_y = 270
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.fps = 30

scene.world.color = (0.055, 0.065, 0.075)
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"

arm = next((o for o in scene.objects if o.type == "ARMATURE"), None)
if arm is None:
    raise RuntimeError("S armature not found")

if arm.animation_data is None or arm.animation_data.action is None:
    actions = list(bpy.data.actions)
    if not actions:
        raise RuntimeError("S base action not found")
    arm.animation_data_create()
    arm.animation_data.action = actions[0]

base_action = arm.animation_data.action
base_start = float(base_action.frame_range[0])
base_end = float(base_action.frame_range[1])
base_span = max(base_end - base_start, 1.0)

required = ["root", "pelvis", "spine", "chest", "neck", "head",
            "fore_L_foot", "fore_R_foot", "hind_L_foot", "hind_R_foot"]
missing = [n for n in required if arm.pose.bones.get(n) is None]
if missing:
    raise RuntimeError("Missing S bones: " + ", ".join(missing))

# ---------- helpers ----------
def mesh_world_bounds():
    deps = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    found = False
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(deps)
        for c in ev.bound_box:
            p = ev.matrix_world @ Vector(c)
            mn.x = min(mn.x, p.x); mn.y = min(mn.y, p.y); mn.z = min(mn.z, p.z)
            mx.x = max(mx.x, p.x); mx.y = max(mx.y, p.y); mx.z = max(mx.z, p.z)
            found = True
    if not found:
        raise RuntimeError("No mesh bounds")
    return mn, mx

def bone_world_head(name):
    b = arm.data.bones[name]
    return arm.matrix_world @ b.head_local

def look_at(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def set_base_source_frame(src_index, source_period_frames=23.0):
    phase = (src_index % source_period_frames) / source_period_frames
    f = base_start + phase * base_span
    fi = int(math.floor(f))
    scene.frame_set(fi, subframe=f - fi)
    bpy.context.view_layer.update()
    return f

def local_rotate(name, x=0.0, y=0.0, z=0.0):
    pb = arm.pose.bones[name]
    rot = (
        Matrix.Rotation(x, 4, "X")
        @ Matrix.Rotation(y, 4, "Y")
        @ Matrix.Rotation(z, 4, "Z")
    )
    pb.matrix_basis = pb.matrix_basis @ rot

def value(key, idx):
    arr = sig.get(key) or []
    if not arr:
        return 0.0
    return float(arr[min(max(idx, 0), len(arr)-1)])

def apply_hybrid(src_index, creature_height):
    # Low-gain v1: body dynamics only. Limb chains and tail are untouched.
    hips_v = value("hips_vertical_norm", src_index)
    pp = value("pelvis_pitch_norm", src_index)
    pr = value("pelvis_roll_norm", src_index)
    tp = value("torso_pitch_norm", src_index)
    tr = value("torso_roll_norm", src_index)
    np = value("neck_pitch_norm", src_index)
    hp = value("head_pitch_norm", src_index)

    # Keep whole-body vertical modulation deliberately small so the existing
    # quadruped contact solution stays dominant.
    arm.location.z += creature_height * 0.006 * hips_v

    local_rotate("pelvis",
                 x=math.radians(1.8) * pp,
                 z=math.radians(1.5) * pr)
    local_rotate("spine",
                 x=math.radians(0.9) * tp,
                 z=math.radians(0.6) * tr)
    local_rotate("chest",
                 x=math.radians(1.4) * tp,
                 z=math.radians(0.9) * tr)
    local_rotate("neck", x=math.radians(0.7) * np)
    local_rotate("head", x=math.radians(1.0) * hp)
    bpy.context.view_layer.update()

def pose_foot_world(name):
    pb = arm.pose.bones[name]
    return arm.matrix_world @ pb.tail

def render(path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

# ---------- establish geometry axes ----------
scene.frame_set(int(base_start))
bpy.context.view_layer.update()
mn, mx = mesh_world_bounds()
center = (mn + mx) * 0.5
height = max(mx.z - mn.z, 0.1)
width = max(mx.x - mn.x, mx.y - mn.y, 0.1)
ground_z = mn.z

pelvis_w = bone_world_head("pelvis")
head_w = bone_world_head("head")
forward = head_w - pelvis_w
forward.z = 0
if forward.length < 1e-5:
    forward = Vector((0, 1, 0))
forward.normalize()
side = Vector((-forward.y, forward.x, 0))
side.normalize()

# Ground.
bpy.ops.mesh.primitive_plane_add(size=max(12.0, width * 8.0), location=(center.x, center.y, ground_z - 0.012))
ground = bpy.context.object
mat = bpy.data.materials.new("Gate3Ground")
mat.diffuse_color = (0.15, 0.17, 0.19, 1)
mat.roughness = 1.0
ground.data.materials.append(mat)

# Lighting.
bpy.ops.object.light_add(type="AREA", location=(center.x + side.x*4, center.y + side.y*4, ground_z + height*3))
key = bpy.context.object
key.data.energy = 1200
key.data.shape = "DISK"
key.data.size = 5
look_at(key, center)

bpy.ops.object.light_add(type="AREA", location=(center.x - side.x*3 - forward.x*2, center.y - side.y*3 - forward.y*2, ground_z + height*1.8))
fill = bpy.context.object
fill.data.energy = 650
fill.data.size = 4
look_at(fill, center)

# Camera.
bpy.ops.object.camera_add()
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 55

cam_dist = max(height * 2.8, width * 2.0, 3.0)

def set_camera(mode):
    target = Vector((center.x, center.y, ground_z + height * 0.48))
    if mode == "SIDE":
        loc = target + side * cam_dist
        loc.z = ground_z + height * 0.62
    elif mode == "LOW":
        loc = target + side * (cam_dist * 0.82) - forward * (cam_dist * 0.18)
        loc.z = ground_z + height * 0.22
        target.z = ground_z + height * 0.42
    elif mode == "CHASE":
        loc = target - forward * (cam_dist * 1.02)
        loc.z = ground_z + height * 0.55
    elif mode == "FRONT":
        loc = target + forward * (cam_dist * 1.02)
        loc.z = ground_z + height * 0.55
    else:
        raise ValueError(mode)
    cam.location = loc
    look_at(cam, target)
    bpy.context.view_layer.update()

samples = [6, 30, 54]
foot_names = ["fore_L_foot", "fore_R_foot", "hind_L_foot", "hind_R_foot"]
arm_base_location = arm.location.copy()
metrics = {
    "asset": str(asset_path),
    "base_action": base_action.name,
    "base_action_frame_range": [base_start, base_end],
    "source_period_frames": 23.0,
    "samples": samples,
    "gains": {
        "root_vertical_height_fraction": 0.006,
        "pelvis_pitch_deg": 1.8,
        "pelvis_roll_deg": 1.5,
        "spine_pitch_deg": 0.9,
        "spine_roll_deg": 0.6,
        "chest_pitch_deg": 1.4,
        "chest_roll_deg": 0.9,
        "neck_pitch_deg": 0.7,
        "head_pitch_deg": 1.0,
    },
    "foot_world_delta": [],
}

modes = ["SIDE", "LOW", "CHASE", "FRONT"]
for mode in modes:
    set_camera(mode)
    for variant in ("baseline", "hybrid"):
        variant_dir = out_dir / "renders" / mode / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        for k, src_idx in enumerate(samples):
            arm.location = arm_base_location.copy()
            base_frame = set_base_source_frame(src_idx)

            baseline_feet = {n: pose_foot_world(n).copy() for n in foot_names}
            if variant == "hybrid":
                apply_hybrid(src_idx, height)
                hybrid_feet = {n: pose_foot_world(n).copy() for n in foot_names}
                if mode == "SIDE":
                    metrics["foot_world_delta"].append({
                        "source_frame": src_idx,
                        "base_frame": base_frame,
                        "feet": {
                            n: {
                                "delta_length": (hybrid_feet[n] - baseline_feet[n]).length,
                                "delta_z": hybrid_feet[n].z - baseline_feet[n].z,
                            } for n in foot_names
                        }
                    })

            render(variant_dir / f"{k:02d}.png")

# Summaries for how strongly the hybrid perturbs contact geometry.
all_d = []
all_z = []
for item in metrics["foot_world_delta"]:
    for f in item["feet"].values():
        all_d.append(abs(f["delta_length"]))
        all_z.append(abs(f["delta_z"]))
metrics["foot_delta_summary"] = {
    "max_world_delta": max(all_d) if all_d else 0.0,
    "mean_world_delta": sum(all_d)/len(all_d) if all_d else 0.0,
    "max_vertical_delta": max(all_z) if all_z else 0.0,
    "creature_height": height,
    "max_delta_height_fraction": (max(all_d)/height) if all_d else 0.0,
}

(out_dir / "gate3-metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print("GATE3_METRICS=" + json.dumps(metrics["foot_delta_summary"], separators=(",", ":")))

import bpy
import json
import math
import os
import sys
from mathutils import Vector


def cli_args():
    args = sys.argv
    if "--" not in args:
        raise SystemExit("Expected: blender --background --python script.py -- input.glb output.glb metadata.json")
    user = args[args.index("--") + 1:]
    if len(user) != 3:
        raise SystemExit("Expected exactly three arguments: input.glb output.glb metadata.json")
    return user


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def join_meshes():
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("No mesh objects found after GLB import")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return mesh


def bounds(mesh):
    coords = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    xs = [v.x for v in coords]
    ys = [v.y for v in coords]
    zs = [v.z for v in coords]
    return coords, {
        "min_x": min(xs), "max_x": max(xs),
        "min_y": min(ys), "max_y": max(ys),
        "min_z": min(zs), "max_z": max(zs),
    }


def detect_head_sign(coords, b):
    length = max(1e-6, b["max_z"] - b["min_z"])
    plus_cut = b["max_z"] - length * 0.22
    minus_cut = b["min_z"] + length * 0.22
    plus = [v.y for v in coords if v.z >= plus_cut]
    minus = [v.y for v in coords if v.z <= minus_cut]
    plus_score = max(plus) if plus else b["min_y"]
    minus_score = max(minus) if minus else b["min_y"]
    return 1 if plus_score >= minus_score else -1, plus_score, minus_score


def make_armature(b, head_sign):
    width = b["max_x"] - b["min_x"]
    height = b["max_y"] - b["min_y"]
    length = b["max_z"] - b["min_z"]
    cx = (b["min_x"] + b["max_x"]) * 0.5
    cz = (b["min_z"] + b["max_z"]) * 0.5
    bottom = b["min_y"]

    body_y = bottom + height * 0.58
    shoulder_z = cz + head_sign * length * 0.25
    hip_z = cz - head_sign * length * 0.25
    chest_z = cz + head_sign * length * 0.13
    pelvis_z = cz - head_sign * length * 0.14
    head_z = cz + head_sign * length * 0.47
    tail_z = cz - head_sign * length * 0.48

    side_x = max(width * 0.30, width * 0.18)
    joint_y = bottom + height * 0.47
    knee_y = bottom + height * 0.25
    ankle_y = bottom + height * 0.075
    foot_y = bottom + height * 0.025
    foot_len = length * 0.075

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "EvoWild_S_Armature_V4_IK"
    arm.show_in_front = True
    default = arm.data.edit_bones.get("Bone")
    if default:
        arm.data.edit_bones.remove(default)

    bones = {}

    def add(name, head, tail, parent=None, deform=True):
        bone = arm.data.edit_bones.new(name)
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        bone.use_deform = deform
        if parent:
            bone.parent = bones[parent]
        bones[name] = bone
        return bone

    add("root", (cx, body_y - height * 0.08, cz), (cx, body_y + height * 0.08, cz), deform=False)
    add("pelvis", (cx, body_y - height * 0.01, hip_z), (cx, body_y + height * 0.02, pelvis_z), parent="root")
    add("spine", (cx, body_y + height * 0.01, pelvis_z), (cx, body_y + height * 0.05, chest_z), parent="pelvis")
    add("chest", (cx, body_y + height * 0.04, chest_z), (cx, body_y + height * 0.07, shoulder_z), parent="spine")
    add("neck", (cx, body_y + height * 0.05, shoulder_z), (cx, body_y + height * 0.19, cz + head_sign * length * 0.36), parent="chest")
    add("head", (cx, body_y + height * 0.17, cz + head_sign * length * 0.34), (cx, body_y + height * 0.22, head_z), parent="neck")
    add("tail", (cx, body_y, hip_z), (cx, body_y - height * 0.03, tail_z), parent="pelvis")

    fore_z = cz + head_sign * length * 0.22
    hind_z = cz - head_sign * length * 0.24
    for side_name, sx in (("L", cx + side_x), ("R", cx - side_x)):
        add(f"fore_{side_name}_upper", (sx, joint_y, fore_z), (sx, knee_y, fore_z + head_sign * length * 0.04), parent="chest")
        add(f"fore_{side_name}_lower", (sx, knee_y, fore_z + head_sign * length * 0.04), (sx, ankle_y, fore_z - head_sign * length * 0.01), parent=f"fore_{side_name}_upper")
        add(f"fore_{side_name}_foot", (sx, ankle_y, fore_z - head_sign * length * 0.01), (sx, foot_y, fore_z + head_sign * foot_len), parent=f"fore_{side_name}_lower")
        add(f"hind_{side_name}_upper", (sx, joint_y, hind_z), (sx, knee_y, hind_z - head_sign * length * 0.03), parent="pelvis")
        add(f"hind_{side_name}_lower", (sx, knee_y, hind_z - head_sign * length * 0.03), (sx, ankle_y, hind_z + head_sign * length * 0.025), parent=f"hind_{side_name}_upper")
        add(f"hind_{side_name}_foot", (sx, ankle_y, hind_z + head_sign * length * 0.025), (sx, foot_y, hind_z + head_sign * foot_len), parent=f"hind_{side_name}_lower")

        # Root-level non-deform controls. They are exported only for this proof;
        # the mesh remains weighted exclusively to the deform chain.
        pole_x = sx + (width * 0.55 if side_name == "L" else -width * 0.55)
        add(f"fore_{side_name}_target", (sx, foot_y, fore_z), (sx, foot_y + height * 0.06, fore_z), deform=False)
        add(f"fore_{side_name}_pole", (pole_x, knee_y, fore_z), (pole_x, knee_y + height * 0.06, fore_z), deform=False)
        add(f"hind_{side_name}_target", (sx, foot_y, hind_z), (sx, foot_y + height * 0.06, hind_z), deform=False)
        add(f"hind_{side_name}_pole", (pole_x, knee_y, hind_z), (pole_x, knee_y + height * 0.06, hind_z), deform=False)

    bpy.ops.object.mode_set(mode="OBJECT")

    for limb in ("fore_L", "fore_R", "hind_L", "hind_R"):
        lower = arm.pose.bones.get(f"{limb}_lower")
        ik = lower.constraints.new(type="IK")
        ik.name = f"{limb}_ground_ik"
        ik.target = arm
        ik.subtarget = f"{limb}_target"
        ik.pole_target = arm
        ik.pole_subtarget = f"{limb}_pole"
        ik.chain_count = 2
        ik.use_tail = True
    return arm, {
        "width": width,
        "height": height,
        "length": length,
        "center": [cx, body_y, cz],
        "head_sign": head_sign,
    }


def segment_distance(point, a, b):
    ab = b - a
    denom = ab.length_squared
    if denom <= 1e-12:
        return (point - a).length
    t = max(0.0, min(1.0, (point - a).dot(ab) / denom))
    closest = a + ab * t
    return (point - closest).length


def deterministic_weights(mesh, arm, dims):
    for group in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(group)

    deform_bones = [bone for bone in arm.data.bones if bone.use_deform]
    groups = {bone.name: mesh.vertex_groups.new(name=bone.name) for bone in deform_bones}

    width = max(1e-6, dims["width"])
    height = max(1e-6, dims["height"])
    length = max(1e-6, dims["length"])
    cx, _, cz = dims["center"]
    head_sign = dims["head_sign"]
    scale = max(width, height, length)
    min_y = min((v.co.y for v in mesh.data.vertices), default=0.0)

    segments = {
        bone.name: (arm.matrix_world @ bone.head_local, arm.matrix_world @ bone.tail_local)
        for bone in deform_bones
    }

    assigned = 0
    for vertex in mesh.data.vertices:
        world = mesh.matrix_world @ vertex.co
        yn = (world.y - min_y) / height
        longitudinal = (world.z - cz) * head_sign
        side = 1 if world.x >= cx else -1
        scored = []

        for bone in deform_bones:
            name = bone.name
            a, c = segments[name]
            d = segment_distance(world, a, c)
            penalty = 1.0

            if "_L_" in name and side < 0:
                penalty *= 7.0
            if "_R_" in name and side > 0:
                penalty *= 7.0

            if name.startswith("fore_") and longitudinal < -length * 0.02:
                penalty *= 6.0
            if name.startswith("hind_") and longitudinal > length * 0.02:
                penalty *= 6.0

            if ("fore_" in name or "hind_" in name) and yn > 0.68:
                penalty *= 5.5
            if name.endswith("_foot") and yn > 0.22:
                penalty *= 10.0
            if name.endswith("_upper") and yn < 0.10:
                penalty *= 3.0

            if name in {"head", "neck"} and longitudinal < length * 0.18:
                penalty *= 4.0
            if name == "tail" and longitudinal > -length * 0.18:
                penalty *= 4.0
            if name in {"pelvis", "spine", "chest"} and yn < 0.32:
                penalty *= 3.2

            score = 1.0 / max((d * penalty / scale) ** 2, 1e-5)
            scored.append((score, name))

        scored.sort(reverse=True)
        top = scored[:4]
        total = sum(score for score, _ in top)
        if total <= 0:
            continue
        for score, name in top:
            groups[name].add([vertex.index], score / total, "REPLACE")
        assigned += 1

    modifier = mesh.modifiers.new(name="EvoWild_Armature_V3", type="ARMATURE")
    modifier.object = arm
    mesh.parent = arm
    return assigned / max(1, len(mesh.data.vertices))


def animate_run_cycle(arm, dims):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 25
    scene.render.fps = 24

    action = bpy.data.actions.new("EvoWild_S_Run_V4_IK")
    arm.animation_data_create()
    arm.animation_data.action = action

    frames = list(range(1, 26, 2))
    if frames[-1] != 25:
        frames.append(25)

    phase_offsets = {
        "hind_L": 0.00,
        "hind_R": 0.43,
        "fore_L": 0.54,
        "fore_R": 0.94,
    }

    length = dims["length"]
    height = dims["height"]
    head_sign = dims["head_sign"]

    def smooth01(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3.0 - 2.0 * x)

    def lerp(a, b, t):
        return a + (b - a) * smooth01(t)

    def contact_target(u, is_hind):
        # Long stance window with exactly zero vertical target offset.
        # Relative Z travels backward while the race parent moves forward.
        # Runtime cadence syncing then maps this clip-space plant to live speed.
        if u < 0.40:
            t = u / 0.40
            z = lerp(0.25, -0.25, t)
            y = 0.0
            foot = -0.08
        elif u < 0.50:
            t = (u - 0.40) / 0.10
            z = lerp(-0.25, -0.34, t)
            y = lerp(0.0, 0.055, t)
            foot = lerp(-0.08, 0.22, t)
        elif u < 0.78:
            t = (u - 0.50) / 0.28
            z = lerp(-0.34, 0.30 if is_hind else 0.27, t)
            y = lerp(0.055, 0.22, math.sin(min(1.0, t) * math.pi * 0.5))
            foot = lerp(0.22, -0.20, t)
        else:
            t = (u - 0.78) / 0.22
            z = lerp(0.30 if is_hind else 0.27, 0.25, t)
            y = lerp(0.22, 0.0, t)
            foot = lerp(-0.20, -0.08, t)
        return z * length, y * height, foot

    def set_rot(name, frame, x=0.0, y=0.0, z=0.0):
        pb = arm.pose.bones.get(name)
        if not pb:
            return
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (x, y, z)
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    def set_target(name, frame, dz, dy):
        pb = arm.pose.bones.get(name)
        if not pb:
            return
        pb.location = (0.0, dy, head_sign * dz)
        pb.keyframe_insert(data_path="location", frame=frame)

    for frame in frames:
        cycle = (frame - 1) / 24.0
        base = cycle * math.tau
        lifts = []

        for limb, offset in phase_offsets.items():
            u = (cycle + offset) % 1.0
            is_hind = limb.startswith("hind")
            z, y, foot_x = contact_target(u, is_hind)
            set_target(f"{limb}_target", frame, z, y)
            set_rot(f"{limb}_foot", frame, foot_x)
            lifts.append(y / max(height, 1e-6))

        airborne = sum(1.0 if value > 0.035 else 0.0 for value in lifts) / len(lifts)
        set_rot("pelvis", frame, 0.024 * math.sin(base - 0.22))
        set_rot("spine", frame, 0.026 * math.sin(base + 0.12))
        set_rot("chest", frame, -0.020 * math.sin(base + 0.32))
        set_rot("neck", frame, -0.026 * math.sin(base + 0.06))
        set_rot("head", frame, -0.014 * math.sin(base - 0.02))
        set_rot("tail", frame, 0.064 * math.sin(base + math.pi * 0.62))

        arm.location.y = height * 0.011 * (airborne - 0.42)
        arm.keyframe_insert(data_path="location", frame=frame, index=1)
        arm.location.z = head_sign * length * 0.0018 * math.sin(base - 0.68)
        arm.keyframe_insert(data_path="location", frame=frame, index=2)

    arm.location.y = 0.0
    arm.location.z = 0.0

    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"

    return action

def main():
    input_path, output_path, metadata_path = cli_args()
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    metadata_path = os.path.abspath(metadata_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=input_path)
    mesh = join_meshes()
    coords, b = bounds(mesh)
    head_sign, plus_score, minus_score = detect_head_sign(coords, b)
    arm, dims = make_armature(b, head_sign)
    coverage = deterministic_weights(mesh, arm, dims)
    action = animate_run_cycle(arm, dims)

    bpy.context.scene.frame_set(1)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        export_animations=True,
        export_force_sampling=True,
        export_yup=True
    )

    metadata = {
        "input": os.path.basename(input_path),
        "output": os.path.basename(output_path),
        "mesh_vertices": len(mesh.data.vertices),
        "mesh_polygons": len(mesh.data.polygons),
        "armature": arm.name,
        "deform_bones": [bone.name for bone in arm.data.bones if bone.use_deform],
        "bone_count": len(arm.data.bones),
        "weight_coverage": round(coverage, 6),
        "head_sign": head_sign,
        "head_detection": {
            "positive_end_max_y": round(plus_score, 6),
            "negative_end_max_y": round(minus_score, 6),
        },
        "bounds": {k: round(v, 6) for k, v in b.items()},
        "animation": {
            "name": action.name,
            "frame_start": 1,
            "frame_end": 25,
            "fps": 24,
        },
        "status": "ik_contact_rig_v4_proof_not_final_art"
    }
    with open(metadata_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
        raise RuntimeError("Rigged GLB export missing or too small")
    print("RIG_V4_IK", json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()

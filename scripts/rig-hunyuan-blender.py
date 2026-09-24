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
    head_z = cz + head_sign * length * 0.47
    tail_z = cz - head_sign * length * 0.48

    side_x = max(width * 0.28, width * 0.16)
    hip_y = bottom + height * 0.48
    knee_y = bottom + height * 0.25
    foot_y = bottom + height * 0.025

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "EvoWild_S_Armature"
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
    add("spine", (cx, body_y, hip_z), (cx, body_y + height * 0.05, shoulder_z), parent="root")
    add("neck", (cx, body_y + height * 0.04, shoulder_z), (cx, body_y + height * 0.20, cz + head_sign * length * 0.36), parent="spine")
    add("head", (cx, body_y + height * 0.18, cz + head_sign * length * 0.34), (cx, body_y + height * 0.22, head_z), parent="neck")
    add("tail", (cx, body_y, hip_z), (cx, body_y - height * 0.02, tail_z), parent="root")

    fore_z = cz + head_sign * length * 0.22
    hind_z = cz - head_sign * length * 0.24
    for side_name, sx in (("L", cx + side_x), ("R", cx - side_x)):
        add(f"fore_{side_name}_upper", (sx, hip_y, fore_z), (sx, knee_y, fore_z + head_sign * length * 0.035), parent="spine")
        add(f"fore_{side_name}_lower", (sx, knee_y, fore_z + head_sign * length * 0.035), (sx, foot_y, fore_z - head_sign * length * 0.015), parent=f"fore_{side_name}_upper")
        add(f"hind_{side_name}_upper", (sx, hip_y, hind_z), (sx, knee_y, hind_z - head_sign * length * 0.025), parent="root")
        add(f"hind_{side_name}_lower", (sx, knee_y, hind_z - head_sign * length * 0.025), (sx, foot_y, hind_z + head_sign * length * 0.02), parent=f"hind_{side_name}_upper")

    bpy.ops.object.mode_set(mode="OBJECT")
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
    scale = max(width, height, length)
    min_vertex_y = min((v.co.y for v in mesh.data.vertices), default=0.0)

    bone_segments = {
        bone.name: (arm.matrix_world @ bone.head_local, arm.matrix_world @ bone.tail_local)
        for bone in deform_bones
    }

    assigned = 0
    for vertex in mesh.data.vertices:
        world = mesh.matrix_world @ vertex.co
        scored = []

        for bone in deform_bones:
            name = bone.name
            a, c = bone_segments[name]
            d = segment_distance(world, a, c)
            penalty = 1.0

            yn = (world.y - min_vertex_y) / max(height, 1e-6)
            if ("fore_" in name or "hind_" in name) and yn > 0.66:
                penalty *= 4.5
            if name in {"head", "neck"} and abs(world.z - dims["center"][2]) < length * 0.12:
                penalty *= 2.2
            if name == "tail" and abs(world.z - dims["center"][2]) < length * 0.12:
                penalty *= 2.0

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

    modifier = mesh.modifiers.new(name="EvoWild_Armature", type="ARMATURE")
    modifier.object = arm
    mesh.parent = arm
    return assigned / max(1, len(mesh.data.vertices))


def animate_run_cycle(arm, dims):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 25
    scene.render.fps = 24

    action = bpy.data.actions.new("EvoWild_S_Run")
    arm.animation_data_create()
    arm.animation_data.action = action

    upper = {
        "fore_L_upper": 1,
        "fore_R_upper": -1,
        "hind_L_upper": -1,
        "hind_R_upper": 1,
    }
    lower = {
        "fore_L_lower": 1,
        "fore_R_lower": -1,
        "hind_L_lower": -1,
        "hind_R_lower": 1,
    }

    frames = [1, 7, 13, 19, 25]
    wave = [0.48, 0.0, -0.48, 0.0, 0.48]
    flex = [0.18, 0.52, 0.78, 0.52, 0.18]

    for bone_name, phase in upper.items():
        pb = arm.pose.bones.get(bone_name)
        pb.rotation_mode = "XYZ"
        for frame, value in zip(frames, wave):
            pb.rotation_euler.x = value * phase
            pb.keyframe_insert(data_path="rotation_euler", frame=frame, index=0)

    for bone_name, phase in lower.items():
        pb = arm.pose.bones.get(bone_name)
        pb.rotation_mode = "XYZ"
        for frame, value in zip(frames, flex):
            pb.rotation_euler.x = value * (1 if phase > 0 else 0.86)
            pb.keyframe_insert(data_path="rotation_euler", frame=frame, index=0)

    spine = arm.pose.bones.get("spine")
    neck = arm.pose.bones.get("neck")
    if spine:
        spine.rotation_mode = "XYZ"
    if neck:
        neck.rotation_mode = "XYZ"

    for frame, body_value, head_value in [
        (1, -0.035, 0.025),
        (7, 0.020, -0.018),
        (13, -0.035, 0.025),
        (19, 0.020, -0.018),
        (25, -0.035, 0.025),
    ]:
        if spine:
            spine.rotation_euler.x = body_value
            spine.keyframe_insert(data_path="rotation_euler", frame=frame, index=0)
        if neck:
            neck.rotation_euler.x = head_value
            neck.keyframe_insert(data_path="rotation_euler", frame=frame, index=0)

    base_y = arm.location.y
    bob = dims["height"] * 0.018
    for frame, offset in [(1, 0), (7, bob), (13, 0), (19, bob), (25, 0)]:
        arm.location.y = base_y + offset
        arm.keyframe_insert(data_path="location", frame=frame, index=1)
    arm.location.y = base_y

    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"

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
        "status": "heuristic_rig_proof_not_final_art"
    }
    with open(metadata_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
        raise RuntimeError("Rigged GLB export missing or too small")
    print("RIG_PROOF", json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()

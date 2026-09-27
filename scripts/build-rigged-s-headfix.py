import bpy, json, math, sys
from mathutils import Vector

args = sys.argv
sep = args.index("--")
src, out, report_path = args[sep + 1: sep + 4]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=src)

mesh = next((o for o in bpy.context.scene.objects if o.type == "MESH" and "head" in o.vertex_groups), None)
arm = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
if mesh is None or arm is None:
    raise RuntimeError("rigged S mesh/armature not found")

head_group = mesh.vertex_groups["head"]
head_bone = arm.data.bones.get("head")
if head_bone is None:
    raise RuntimeError("head bone not found")

center_world = arm.matrix_world @ head_bone.head_local
center_x = center_world.x

pts = []
for v in mesh.data.vertices:
    try:
        w = head_group.weight(v.index)
    except RuntimeError:
        continue
    if w < 0.18:
        continue
    p = mesh.matrix_world @ v.co
    pts.append((v, p, w))

if not pts:
    raise RuntimeError("no head-weighted vertices")

min_y = min(p.y for _, p, _ in pts)
max_y = max(p.y for _, p, _ in pts)
min_z = min(p.z for _, p, _ in pts)
max_z = max(p.z for _, p, _ in pts)

# The visible fork is not the face itself. It is the high, swept-back crest:
# high Y and relatively rearward Z (less negative than the muzzle/head bone).
y_start = min_y + (max_y - min_y) * 0.60
z_start = -0.50
inv = mesh.matrix_world.inverted()
changed = 0
max_shift = 0.0

def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)

for v, p, weight in pts:
    if p.y <= y_start or p.z <= z_start:
        continue

    hy = smooth01((p.y - y_start) / max(1e-6, max_y - y_start))
    hz = smooth01((p.z - z_start) / max(1e-6, max_z - z_start))
    hw = smooth01((weight - 0.18) / 0.45)
    strength = hy * (0.55 + 0.45 * hz) * (0.70 + 0.30 * hw)

    # Preserve the broad horn base while bringing the two upper lobes close
    # enough to read as a single swept crest rather than a split head.
    scale_x = 1.0 - 0.58 * strength
    old_x = p.x
    p.x = center_x + (p.x - center_x) * scale_x

    # Small rearward convergence avoids a flat "pinched" front silhouette.
    p.z -= 0.012 * strength

    v.co = inv @ p
    changed += 1
    max_shift = max(max_shift, abs(old_x - p.x))

mesh.data.update()

# Recalculate normals without changing topology/weights.
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")
mesh.select_set(False)

bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    export_animations=True,
    export_skins=True,
    export_morph=False,
    export_yup=True
)

report = {
    "source": src,
    "output": out,
    "changed_vertices": changed,
    "max_x_shift": max_shift,
    "head_center_x": center_x,
    "y_start": y_start,
    "z_start": z_start,
    "head_bounds": {
        "min_y": min_y, "max_y": max_y,
        "min_z": min_z, "max_z": max_z
    },
    "status": "rigged_headfix_v1_candidate"
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("S_HEADFIX_REPORT " + json.dumps(report, separators=(",", ":")))

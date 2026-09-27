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
#
# v1 scaled both lobes toward the centre. That reduced the gap but also
# narrowed each lobe, which produced the needle-like FRONT silhouette seen in
# the NPR review. v2 keeps each lobe's own width and translates the two upper
# clusters toward each other so their inner edges overlap slightly.
height = max_y - min_y
y_measure = min_y + height * 0.62
y_blend = min_y + height * 0.50
z_start = -0.50
side_guard = 0.0035

crest = []
for v, p, weight in pts:
    if p.y < y_measure or p.z <= z_start:
        continue
    dx = p.x - center_x
    if abs(dx) <= side_guard:
        continue
    crest.append((v, p.copy(), weight, dx))

left = [(v, p, w, dx) for v, p, w, dx in crest if dx < 0]
right = [(v, p, w, dx) for v, p, w, dx in crest if dx > 0]
if len(left) < 4 or len(right) < 4:
    raise RuntimeError(f"not enough crest vertices: left={len(left)} right={len(right)}")

left_centroid = sum(p.x for _, p, _, _ in left) / len(left)
right_centroid = sum(p.x for _, p, _, _ in right) / len(right)
left_min = min(p.x for _, p, _, _ in left)
left_max = max(p.x for _, p, _, _ in left)
right_min = min(p.x for _, p, _, _ in right)
right_max = max(p.x for _, p, _, _ in right)

left_half = max(0.0025, (left_max - left_min) * 0.5)
right_half = max(0.0025, (right_max - right_min) * 0.5)
overlap = min(left_half, right_half) * 0.22

# Preserve lobe width. Only translate the lobes until their inner edges pass
# the centreline slightly. This gives one continuous skull/crest mass from
# FRONT while retaining the original two swept tips and SIDE profile.
left_target_centroid = center_x + overlap - left_half
right_target_centroid = center_x - overlap + right_half
left_shift = left_target_centroid - left_centroid
right_shift = right_target_centroid - right_centroid

inv = mesh.matrix_world.inverted()
changed = 0
max_shift = 0.0

def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)

for v, p, weight in pts:
    if p.y <= y_blend or p.z <= z_start:
        continue

    dx = p.x - center_x
    if abs(dx) <= side_guard * 0.5:
        continue

    hy = smooth01((p.y - y_blend) / max(1e-6, y_measure - y_blend))
    hz = smooth01((p.z - z_start) / max(1e-6, max_z - z_start))
    hw = smooth01((weight - 0.18) / 0.45)
    strength = hy * (0.70 + 0.30 * hz) * (0.72 + 0.28 * hw)

    shift = left_shift if dx < 0 else right_shift
    old_x = p.x
    p.x += shift * strength

    # Tiny rearward convergence prevents a flat frontal slab while keeping the
    # side silhouette almost unchanged.
    p.z -= 0.004 * strength

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
    "y_measure": y_measure,
    "y_blend": y_blend,
    "z_start": z_start,
    "left_count": len(left),
    "right_count": len(right),
    "left_half_width": left_half,
    "right_half_width": right_half,
    "overlap": overlap,
    "left_shift": left_shift,
    "right_shift": right_shift,
    "head_bounds": {
        "min_y": min_y, "max_y": max_y,
        "min_z": min_z, "max_z": max_z
    },
    "status": "rigged_headfix_v2_width_preserving_candidate"
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("S_HEADFIX_REPORT " + json.dumps(report, separators=(",", ":")))

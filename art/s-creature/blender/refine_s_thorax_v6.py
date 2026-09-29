"""Deterministic v6 anterior-thorax correction from S-blockout-v5.

Applies exactly one local displacement pass to the integrated S mesh.
Locks X, topology, vertex count, lower-neck width, forelimb roots, scapular keels,
and all geometry outside the specified anterior-thorax region.
"""
import bpy, os, json
from mathutils.bvhtree import BVHTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")

source = bpy.data.collections.get("S_EDITABLE_SOURCE")
model = bpy.data.collections.get("S_MODEL")
if source is None or model is None:
    raise RuntimeError("Missing S_EDITABLE_SOURCE or S_MODEL")

body = next((o for o in model.objects if o.type == "MESH"), None)
if body is None:
    raise RuntimeError("No integrated S mesh found")

protected = [
    o for o in source.objects
    if o.type == "MESH" and (
        o.name.startswith("Forelimb")
        or o.name.startswith("Scapular_keel")
        or o.name.startswith("Neck_integrated_keel")
    )
]
if not protected:
    raise RuntimeError("No protected Forelimb/Scapular_keel/Neck_integrated_keel meshes found")

depsgraph = bpy.context.evaluated_depsgraph_get()
bvhs = []
for obj in protected:
    eo = obj.evaluated_get(depsgraph)
    me = eo.to_mesh()
    try:
        verts = [eo.matrix_world @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        if verts and polys:
            bvhs.append((obj.name, BVHTree.FromPolygons(verts, polys, all_triangles=False)))
    finally:
        eo.to_mesh_clear()

if not bvhs:
    raise RuntimeError("Protected-surface BVHs could not be built")

def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t*t*(3.0 - 2.0*t)

def bump(q, lo, peak, hi):
    if q <= lo or q >= hi:
        return 0.0
    if q <= peak:
        return smooth01((q-lo)/(peak-lo))
    return smooth01((hi-q)/(hi-peak))

original = [v.co.copy() for v in body.data.vertices]
changed = []
max_w = 0.0
min_protected_distance = None

body_to_world = body.matrix_world
world_to_body = body.matrix_world.inverted()

for i, v in enumerate(body.data.vertices):
    p = v.co.copy()
    x, y, z = p.x, p.y, p.z

    if not (abs(x) < 0.20 and -1.06 < y < -0.48 and 1.76 < z < 2.28):
        continue

    w = (
        (1.0 - smooth01((abs(x)-0.08)/0.12))
        * bump(y, -1.06, -0.84, -0.48)
        * bump(z, 1.76, 2.03, 2.28)
    )
    if w <= 0.0:
        continue

    pw = body_to_world @ p
    d = None
    for _name, bvh in bvhs:
        hit = bvh.find_nearest(pw)
        if hit is None:
            continue
        dist = hit[3]
        d = dist if d is None else min(d, dist)
    if d is None:
        raise RuntimeError("Protected-surface distance query failed")

    min_protected_distance = d if min_protected_distance is None else min(min_protected_distance, d)
    w *= smooth01((d - 0.04)/0.08)
    if w <= 0.0:
        continue

    # Apply from the original coordinate once only.
    p2 = p.copy()
    p2.y = y + 0.060*w
    p2.z = z + 0.085*w
    p2.x = x
    v.co = p2
    changed.append(i)
    max_w = max(max_w, w)

body.data.update()

if not changed:
    raise RuntimeError("v6 correction changed zero vertices")

# Hard validation: X/topology/vertex count/outside region all fixed.
if len(body.data.vertices) != len(original):
    raise RuntimeError("Vertex count changed")
for i, p0 in enumerate(original):
    p1 = body.data.vertices[i].co
    if abs(p1.x - p0.x) > 1e-9:
        raise RuntimeError(f"X changed at vertex {i}")
    if i not in changed and (p1 - p0).length > 1e-9:
        raise RuntimeError(f"Unexpected change outside target set at vertex {i}")

body.name = "S_organism_blockout_v6"
scene = bpy.context.scene
scene.camera = bpy.data.objects.get("CAM_FRONT34")

v6_path = os.path.join(OUT, "S-blockout-v6.blend")
bpy.ops.wm.save_as_mainfile(filepath=v6_path, compress=True)

report = {
    "input": "S-blockout-v5.blend",
    "output": "S-blockout-v6.blend",
    "scope": "anterior thorax lower-front bulge only",
    "target_bounds": {
        "abs_x_lt": 0.20,
        "y": [-1.06, -0.48],
        "z": [1.76, 2.28]
    },
    "max_displacement": {"y_back": 0.060, "z_up": 0.085},
    "changed_vertices": len(changed),
    "total_vertices": len(original),
    "max_weight": max_w,
    "min_protected_surface_distance_seen": min_protected_distance,
    "protected_object_count": len(bvhs),
    "lateral_x_unchanged": True,
    "topology_unchanged": True,
    "vertex_count_unchanged": True,
    "neck_width_reduction_preserved": True,
    "accepted": False
}
with open(os.path.join(OUT, "thorax-v6-validation.json"), "w") as f:
    json.dump(report, f, indent=2)

hp = os.path.join(ROOT, "HANDOFF_STATE.json")
state = json.load(open(hp))
state.update(
    stage="S-blockout-v6",
    current_stage="S-blockout-v6 anterior thorax correction saved, review pending",
    current_model_file="output/S-blockout-v6.blend",
    next_action="Inspect the anterior thorax / shoulder / chest transition in v6 review renders against reference 01 and decide KEEP or REVISE.",
    blockers=[],
    accepted=False
)
json.dump(state, open(hp, "w"), ensure_ascii=False, indent=2)

cp = os.path.join(ROOT, "CHECKPOINT.md")
s = open(cp).read()
lines = []
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line = "current_stage: S-blockout-v6 anterior thorax correction saved, review pending"
    elif line.startswith("current_model_file:"):
        line = "current_model_file: output/S-blockout-v6.blend"
    elif line.startswith("next_action:"):
        line = "next_action: Inspect the anterior thorax / shoulder / chest transition in v6 review renders against reference 01 and decide KEEP or REVISE."
    lines.append(line)
s = "\n".join(lines) + "\n"
if "Applied v6 anterior-thorax correction" not in s:
    insert = "- Applied v6 anterior-thorax correction once: central lower-front chest moved backward/upward under the specified smooth bounds while X, topology, vertex count, neck width, forelimb/scapular protected surfaces, and all other regions remained fixed.\n"
    s = s.replace("next_action:", insert + "\nnext_action:", 1)
open(cp, "w").write(s)

print("S_V6", json.dumps(report))

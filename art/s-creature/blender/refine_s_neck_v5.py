"""Second deterministic lower-neck/chest ventral correction from S-blockout-v4.
Scope lock: no topology change, no lateral-width change, no skull/crest edit.
"""
import bpy, os, json, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")

source = bpy.data.collections.get("S_EDITABLE_SOURCE")
model = bpy.data.collections.get("S_MODEL")
if source is None or model is None:
    raise RuntimeError("Required S_EDITABLE_SOURCE or S_MODEL collection missing")

neck = next((o for o in source.objects if o.name.startswith("Neck_integrated_keel")), None)
body = next((o for o in model.objects if o.type == "MESH"), None)
if neck is None or body is None:
    raise RuntimeError("Required neck source or continuous body mesh missing")

ring_size = 16
verts = list(neck.data.vertices)
if len(verts) < ring_size * 3 or len(verts) % ring_size != 0:
    raise RuntimeError("Unexpected Neck_integrated_keel ring layout")
rings = [verts[i:i+ring_size] for i in range(0, len(verts), ring_size)]

def section_frame(ring):
    pts = [v.co.copy() for v in ring]
    c = sum(pts, Vector()) / len(pts)
    d = max(pts, key=lambda p: p.z)
    v = min(pts, key=lambda p: p.z)
    n = (v - d).normalized()
    h = (v - d).length
    return c, d, n, h

frames = [section_frame(r) for r in rings]
# Neck side -> chest side: ring 2 -> ring 1 -> ring 0.
idx = [2, 1, 0]

def smooth(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x-a)/(b-a)))
    return t*t*(3.0-2.0*t)

def closest_frame(p):
    best = None
    for seg in range(2):
        ia, ib = idx[seg], idx[seg+1]
        ca, cb = frames[ia][0], frames[ib][0]
        axis = cb - ca
        u = max(0.0, min(1.0, (p-ca).dot(axis) / max(axis.length_squared, 1e-12)))
        c = ca + axis*u
        dist2 = (p-c).length_squared
        t = (seg + u) / 2.0
        if best is None or dist2 < best[0]:
            # Interpolate dorsal point, ventral direction and dorsal-ventral diameter.
            da, na, ha = frames[ia][1], frames[ia][2], frames[ia][3]
            db, nb, hb = frames[ib][1], frames[ib][2], frames[ib][3]
            d = da.lerp(db, u)
            n = na.lerp(nb, u).normalized()
            h = ha*(1.0-u) + hb*u
            best = (dist2, t, c, d, n, h)
    return best

original = [v.co.copy() for v in body.data.vertices]
changed = []
strength = 0.18

for i, vert in enumerate(body.data.vertices):
    p = vert.co.copy()
    dist2, t, c, d, n, h = closest_frame(p)

    # Compact support around the lower-neck/chest transition only.
    radial = math.sqrt(dist2)
    w_rad = 1.0 - smooth(0.30, 0.48, radial)
    w_t = math.sin(math.pi * t) ** 2
    q = (p - d).dot(n)
    ventral_excess = max(0.0, q - h/2.0)
    amount = strength * w_t * w_rad * ventral_excess

    if amount <= 1e-9:
        continue

    newp = p - n * amount
    # Hard lock lateral width.
    newp.x = p.x
    vert.co = newp
    changed.append(i)

body.data.update()

if not changed:
    raise RuntimeError("v5 correction changed zero vertices")

# Hard scope checks.
for i, p0 in enumerate(original):
    p1 = body.data.vertices[i].co
    if abs(p1.x - p0.x) > 1e-8:
        raise RuntimeError("Lateral width changed unexpectedly")
# Head/crest-side points well forward of the transition remain unchanged.
for i, p0 in enumerate(original):
    if p0.y < -1.50 and (body.data.vertices[i].co - p0).length > 1e-8:
        raise RuntimeError("Head/crest-protected region changed unexpectedly")

body.name = "S_organism_blockout_v5"
scene = bpy.context.scene
scene.camera = bpy.data.objects.get("CAM_FRONT34")
v5_path = os.path.join(OUT, "S-blockout-v5.blend")
bpy.ops.wm.save_as_mainfile(filepath=v5_path, compress=True)

report = {
    "input": "S-blockout-v4.blend",
    "output": "S-blockout-v5.blend",
    "scope": "lower neck/chest ventral transition only",
    "second_pass_strength": strength,
    "changed_vertices": len(changed),
    "total_vertices": len(original),
    "lateral_width_unchanged": True,
    "topology_unchanged": True,
    "protected_forward_region_unchanged": True,
    "accepted": False
}
with open(os.path.join(OUT, "neck-v5-validation.json"), "w") as f:
    json.dump(report, f, indent=2)

# Update handoff/checkpoint without touching unrelated quality issues.
hp = os.path.join(ROOT, "HANDOFF_STATE.json")
state = json.load(open(hp))
state.update(
    stage="S-blockout-v5",
    current_stage="S-blockout-v5 second ventral correction saved, review pending",
    current_model_file="output/S-blockout-v5.blend",
    next_action="Inspect only the lower-neck/chest junction in v5 review renders against reference 01 and decide KEEP or REVISE.",
    blockers=[],
    accepted=False
)
json.dump(state, open(hp, "w"), ensure_ascii=False, indent=2)

cp = os.path.join(ROOT, "CHECKPOINT.md")
s = open(cp).read()
lines = []
for line in s.splitlines():
    if line.startswith("current_stage:"):
        line = "current_stage: S-blockout-v5 second ventral correction saved, review pending"
    elif line.startswith("current_model_file:"):
        line = "current_model_file: output/S-blockout-v5.blend"
    elif line.startswith("next_action:"):
        line = "next_action: Inspect only the lower-neck/chest junction in v5 review renders against reference 01 and decide KEEP or REVISE."
    lines.append(line)
s = "\n".join(lines) + "\n"
if "Applied second deterministic ventral-only correction" not in s:
    s = s.replace("next_action:", "- Applied second deterministic ventral-only correction (18% max of ventral excess with smooth section/radial falloff); lateral width/topology/protected forward region unchanged.\n\nnext_action:", 1)
open(cp, "w").write(s)

print("S_V5", json.dumps(report))

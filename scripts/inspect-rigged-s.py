import bpy, json, sys

args = sys.argv
path = args[args.index("--") + 1]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=path)

def world_bounds(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not pts:
        return None
    return {
        "min": [min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)],
        "max": [max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)]
    }

meshes = []
arms = []
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        meshes.append({
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "parent": obj.parent.name if obj.parent else None,
            "parent_type": obj.parent_type,
            "modifiers": [{"name": m.name, "type": m.type, "object": getattr(getattr(m, "object", None), "name", None)} for m in obj.modifiers],
            "vertex_groups": [g.name for g in obj.vertex_groups],
            "materials": [m.name if m else None for m in obj.data.materials],
            "bounds": world_bounds(obj)
        })
    elif obj.type == "ARMATURE":
        bones = []
        for b in obj.data.bones:
            hw = obj.matrix_world @ b.head_local
            tw = obj.matrix_world @ b.tail_local
            bones.append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "head": [hw.x, hw.y, hw.z],
                "tail": [tw.x, tw.y, tw.z],
                "length": b.length
            })
        arms.append({"name": obj.name, "bones": bones})

actions = []
for a in bpy.data.actions:
    actions.append({"name": a.name, "frame_range": [float(a.frame_range[0]), float(a.frame_range[1])], "fcurves": len(a.fcurves)})

print("S_RIG_INSPECT " + json.dumps({
    "meshes": meshes,
    "armatures": arms,
    "actions": actions
}, separators=(",", ":")))


# Head-weighted vertex diagnostics for geometry repair.
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or "head" not in obj.vertex_groups:
        continue
    group = obj.vertex_groups["head"]
    pts = []
    for v in obj.data.vertices:
        try:
            w = group.weight(v.index)
        except RuntimeError:
            continue
        if w < 0.25:
            continue
        p = obj.matrix_world @ v.co
        pts.append((p.x, p.y, p.z, w, v.index))
    if pts:
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        min_z = min(p[2] for p in pts)
        max_z = max(p[2] for p in pts)
        cutoff = min_y + (max_y - min_y) * 0.68
        top = [p for p in pts if p[1] >= cutoff]
        bins = []
        if top:
            xmin = min(p[0] for p in top)
            xmax = max(p[0] for p in top)
            span = max(1e-6, xmax - xmin)
            counts = [0] * 12
            for p in top:
                b = min(11, int((p[0] - xmin) / span * 12))
                counts[b] += 1
            bins = {"xmin": xmin, "xmax": xmax, "counts": counts}
        samples = sorted(top, key=lambda p: p[1], reverse=True)[:32]
        print("S_HEAD_VERTS " + json.dumps({
            "count": len(pts),
            "bounds": {
                "min_x": min(p[0] for p in pts), "max_x": max(p[0] for p in pts),
                "min_y": min_y, "max_y": max_y,
                "min_z": min_z, "max_z": max_z
            },
            "top_cutoff_y": cutoff,
            "top_count": len(top),
            "top_bins_x": bins,
            "top_samples": [
                {"i": p[4], "x": p[0], "y": p[1], "z": p[2], "w": p[3]}
                for p in samples
            ]
        }, separators=(",", ":")))

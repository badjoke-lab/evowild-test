import bpy, json, sys
from pathlib import Path

args = sys.argv
asset = Path(args[args.index("--") + 1])
output = Path(args[args.index("--") + 2])

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(asset))

arms = []
for obj in bpy.context.scene.objects:
    if obj.type != "ARMATURE":
        continue
    bones = []
    for b in obj.data.bones:
        bones.append({
            "name": b.name,
            "parent": b.parent.name if b.parent else None,
            "length": b.length,
            "head_local": list(b.head_local),
            "tail_local": list(b.tail_local),
        })
    arms.append({"name": obj.name, "bones": bones})

actions = []
for a in bpy.data.actions:
    actions.append({
        "name": a.name,
        "frame_range": [float(a.frame_range[0]), float(a.frame_range[1])],
        "fcurve_count": len(a.fcurves),
    })

data = {"asset": str(asset), "armatures": arms, "actions": actions}
output.write_text(json.dumps(data, indent=2), encoding="utf-8")
print("S_RIG_GATE2=" + json.dumps(data, separators=(",", ":")))

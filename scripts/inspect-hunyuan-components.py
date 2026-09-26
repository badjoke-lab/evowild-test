import bpy
import json
import os
import sys
from collections import deque


def cli():
    xs=sys.argv
    if "--" not in xs:
        raise SystemExit("input.glb required")
    return os.path.abspath(xs[xs.index("--")+1])


def obj_bounds(obj):
    pts=[obj.matrix_world @ v.co for v in obj.data.vertices]
    if not pts:
        return None
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    return {
        "min":[min(xs),min(ys),min(zs)],
        "max":[max(xs),max(ys),max(zs)]
    }


def components(obj):
    n=len(obj.data.vertices)
    adj=[[] for _ in range(n)]
    for e in obj.data.edges:
        a,b=e.vertices
        adj[a].append(b); adj[b].append(a)
    seen=[False]*n
    out=[]
    for start in range(n):
        if seen[start]:
            continue
        q=[start]; seen[start]=True; ids=[]
        while q:
            i=q.pop()
            ids.append(i)
            for j in adj[i]:
                if not seen[j]:
                    seen[j]=True; q.append(j)
        pts=[obj.matrix_world @ obj.data.vertices[i].co for i in ids]
        xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
        out.append({
            "vertices":len(ids),
            "min":[min(xs),min(ys),min(zs)],
            "max":[max(xs),max(ys),max(zs)],
            "center":[sum(xs)/len(xs),sum(ys)/len(ys),sum(zs)/len(zs)]
        })
    out.sort(key=lambda x:x["vertices"],reverse=True)
    return out


path=cli()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=path)
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
report=[]
for o in meshes:
    report.append({
        "name":o.name,
        "vertices":len(o.data.vertices),
        "polygons":len(o.data.polygons),
        "bounds":obj_bounds(o),
        "components":components(o)[:40]
    })
print("S_SHAPE_COMPONENTS",json.dumps(report,separators=(",",":")))

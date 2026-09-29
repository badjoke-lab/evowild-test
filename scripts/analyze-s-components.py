import bpy, json, os, sys
from collections import deque

def args():
    xs=sys.argv
    if "--" not in xs: raise SystemExit("need glb out.json")
    a=xs[xs.index("--")+1:]
    if len(a)!=2: raise SystemExit("need 2 args")
    return os.path.abspath(a[0]),os.path.abspath(a[1])

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def join_meshes():
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    if len(meshes)>1:bpy.ops.object.join()
    o=bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return o

def components(obj):
    n=len(obj.data.vertices)
    adj=[[] for _ in range(n)]
    for e in obj.data.edges:
        a,b=e.vertices
        adj[a].append(b);adj[b].append(a)
    seen=[False]*n
    out=[]
    for i in range(n):
        if seen[i]: continue
        q=[i];seen[i]=True;ids=[]
        while q:
            v=q.pop();ids.append(v)
            for nb in adj[v]:
                if not seen[nb]:
                    seen[nb]=True;q.append(nb)
        pts=[obj.matrix_world @ obj.data.vertices[j].co for j in ids]
        xs=[p.x for p in pts];ys=[p.y for p in pts];zs=[p.z for p in pts]
        out.append({
            "size":len(ids),
            "min_x":min(xs),"max_x":max(xs),
            "min_y":min(ys),"max_y":max(ys),
            "min_z":min(zs),"max_z":max(zs),
            "centroid":[sum(xs)/len(xs),sum(ys)/len(ys),sum(zs)/len(zs)]
        })
    out.sort(key=lambda c:c["size"],reverse=True)
    return out

inp,out=args()
clear();bpy.ops.import_scene.gltf(filepath=inp);obj=join_meshes()
data={"vertex_count":len(obj.data.vertices),"edge_count":len(obj.data.edges),"components":components(obj)}
with open(out,"w") as f: json.dump(data,f,indent=2)
print("COMPONENTS",json.dumps(data,separators=(",",":")))

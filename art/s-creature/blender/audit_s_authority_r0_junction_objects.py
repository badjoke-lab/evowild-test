"""Read-only anatomical object ownership audit on accepted R0 scene.

Do not modify any Blender object, geometry, camera or checkpoint.
Find whether visually unsightly shoulder/pelvis roots belong to continuous
body, separate armor, or intersecting mesh.
"""
import bpy,json,os
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output","review","authority-r1-a1-trial")
os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections["S_REBUILD_GATE_A"]
body=bpy.data.objects["S_B2a_v5_continuous_body"]
world=lambda o,v:o.matrix_world@v.co
kdtree=KDTree(len(body.data.vertices))
for i,v in enumerate(body.data.vertices):
    kdtree.insert(world(body,v),i)
kdtree.balance()
entries=[]

def span(vals):
    lo=[min(v[i] for v in vals) for i in range(3)]
    hi=[max(v[i] for v in vals) for i in range(3)]
    return [lo,hi]

for ob in sorted((o for o in cage.objects if o.type=="MESH"),key=lambda o:o.name):
    coords=[world(ob,v) for v in ob.data.vertices]
    if not coords:continue
    box=span(coords)
    shoulder=sum(1 for v in coords if -.18<v.y<.26 and .70<v.z<1.12 and .04<abs(v.x)<.27)
    pelvis=sum(1 for v in coords if .58<v.y<.98 and .70<v.z<1.12 and .04<abs(v.x)<.27)
    sample=coords[::max(1,len(coords)//1200)]
    if ob==body:
        near={"sample_count":len(sample),"near_to_body_vertices":"SELF"}
    else:
        dd=[kdtree.find(p)[2] for p in sample]
        near={
            "sample_count":len(dd),
            "min_nearest_body_vertex":min(dd),
            "mean_nearest_body_vertex":sum(dd)/len(dd),
            "fraction_near_lt_0p025":sum(d<.025 for d in dd)/len(dd),
            "fraction_near_lt_0p05":sum(d<.05 for d in dd)/len(dd)
        }
    entries.append({
       "object":ob.name,
       "vertices":len(ob.data.vertices),
       "polygons":len(ob.data.polygons),
       "bbox_world_xyz":box,
       "inside_fore_support_vertices":shoulder,
       "inside_hind_support_vertices":pelvis,
       "body_surface_vertex_proximity":near,
       "is_continuous_body":ob==body,
    })
report={
 "source":"S-authority-r0-a5-v2.blend",
 "read_only":True,
 "accepted_R0_kept_unchanged":True,
 "object_count":len(entries),
 "continuous_body_vertex_count":len(body.data.vertices),
 "object_evidence":entries,
 "note":"BBox and nearest vertex distance classify ownership and proximity; do not infer exact intersections without a BVH surface test.",
}
p=os.path.join(OUT,"R0_JUNCTION_OBJECT_MAP.json")
with open(p,"w") as f:json.dump(report,f,indent=2)
print(json.dumps({
 "object_count":len(entries),
 "objects":[{
 "name":o["object"],"vertices":o["vertices"],
 "fore":o["inside_fore_support_vertices"],
 "hind":o["inside_hind_support_vertices"],
 "proximity":o["body_surface_vertex_proximity"]} for o in entries]},indent=2))
